from fastapi import APIRouter, HTTPException, Request
from schemas.game_schemas import NewGameRequest, NewGameResponse, PlayMoveRequest, PlayMoveResponse
import uuid
import time
import asyncio

# --- constants ---
WORKER_TIMEOUT = 10   # workers must respond in 10 seconds, otherwise timeout
MAX_SESSIONS = 8      # concurrent session cap

router = APIRouter()

def _dispatch_task(task_queues, results_dict, worker_id: int, command: str, kwargs: dict):
    """
    Blocking helper function. 
    Sends a task to a specific worker and waits for the result.
    """

    task_id = uuid.uuid4().hex
    task_queues[worker_id].put((task_id, command, kwargs))

    # wait for result to appear in results_dict
    start_time = time.time()
    while task_id not in results_dict:
        if time.time() - start_time > WORKER_TIMEOUT:
            raise TimeoutError('Request timed out waiting for chess engine worker')
        
        time.sleep(0.01)

    # retrieve and remove result from shared dict
    status, result_data = results_dict.pop(task_id)

    if status == 'error':
        raise RuntimeError(result_data)
    
    return result_data

@router.post('/new-game', response_model=NewGameResponse)
async def new_game(request: Request, new_game_req: NewGameRequest):
    loop = asyncio.get_running_loop()

    session_count = request.app.state.session_count
    worker_load = request.app.state.worker_load
    session_map = request.app.state.session_map
    task_queues = request.app.state.task_queues
    results_dict = request.app.state.results_dict
    session_count_lock = request.app.state.session_count_lock

    def new_game_task():
        # reserve a session slot, use lock to prevent race conditions
        with session_count_lock:
            if session_count.value >= MAX_SESSIONS:
                raise ValueError('Server is at maximum capacity, please try again later')
            
            session_count.value += 1

        with session_count_lock:
            # find the worker with the least load
            min_load = float('inf')
            target_worker_id = 0
            for i, load in enumerate(worker_load):
                if load < min_load:
                    min_load = load
                    target_worker_id = i
            worker_load[target_worker_id] += 1
        
        try:
            # send task to chosen worker and wait for result
            result = _dispatch_task(
                task_queues, results_dict,
                worker_id=target_worker_id,
                command='new_game',
                kwargs={'player_move': new_game_req.player_move}
            )
            
            new_fen, move_info, game_id = result

        except Exception as e:
            with session_count_lock:
                session_count.value -= 1
                worker_load[target_worker_id] -= 1
            
            raise e
        
        # map the session to its worker
        session_map[game_id] = target_worker_id

        return new_fen, move_info, game_id
            
    try:
        new_fen, move_info, game_id = await loop.run_in_executor(None, new_game_task)
        return NewGameResponse(
            new_fen = new_fen,
            move_played = move_info['move'],
            depth_reached = move_info['depth'],
            nodes_searched = move_info['nodes'],
            is_book = move_info['is_book'],
            game_id = game_id,
        )
    
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except (RuntimeError, TimeoutError) as e:
        print(f"A server-side engine error occurred: {e}")
        raise HTTPException(status_code=500, detail='An internal engine error occurred')
    except Exception as e:
        print(f"An unexpected server error occurred: {e}")
        raise HTTPException(status_code=500, detail='An internal server error occurred')
    
@router.post('/play-move', response_model=PlayMoveResponse)
async def play_move(request: Request, play_move_req: PlayMoveRequest):
    loop = asyncio.get_running_loop()

    session_map = request.app.state.session_map
    task_queues = request.app.state.task_queues
    results_dict = request.app.state.results_dict
    
    def play_move_task():
        session_id = play_move_req.session_id

        # find which worker is handling this game
        target_worker_id = session_map.get(session_id)
        if target_worker_id is None:
            raise KeyError('Invalid or expired session ID')

        # send task to the correct worker and wait
        return _dispatch_task(
            task_queues, results_dict,
            worker_id=target_worker_id,
            command='play_move',
            kwargs={
                'player_move': play_move_req.player_move,
                'session_id': play_move_req.session_id,
                'client_fen': play_move_req.client_fen,
            }
        )
    
    try:
        new_fen, move_info = await loop.run_in_executor(None, play_move_task)

        return PlayMoveResponse(
            new_fen = new_fen,
            move_played = move_info['move'],
            depth_reached = move_info['depth'],
            nodes_searched = move_info['nodes'],
            is_book = move_info['is_book']
        )

    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (RuntimeError, TimeoutError) as e:
        print(f"A server-side engine error occurred: {e}")
        raise HTTPException(status_code=500, detail='An internal engine error occurred')
    except Exception as e:
        print(f"An unexpected server error occurred: {e}")
        raise HTTPException(status_code=500, detail='An internal server error occurred')