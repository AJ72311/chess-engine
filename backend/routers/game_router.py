from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from services import game_service
from schemas.game_schemas import NewGameRequest, NewGameResponse, PlayMoveRequest, PlayMoveResponse

router = APIRouter()

@router.post('/new-game', response_model=NewGameResponse)
async def new_game(request: NewGameRequest):
    try:
        # run search in thread pool to avoid blocking server event loop
        new_game = await run_in_threadpool(game_service.new_game, request.player_move)
        
        new_fen = new_game[0]
        move_info = new_game[1]
        game_id = new_game[2]

        return NewGameResponse(
            new_fen = new_fen,
            move_played = move_info['move'],
            depth_reached = move_info['depth'],
            nodes_searched = move_info['nodes'],
            is_book = move_info['is_book'],
            game_id = game_id,
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except RuntimeError as e:
        print(f"A server-side engine error occurred: {e}")
        raise HTTPException(status_code=500, detail='An internal engine error occurred')

    except Exception as e:
        print(f"An unexpected server error occurred: {e}")
        raise HTTPException(status_code=500, detail='An internal server error occurred')
    
@router.post('/play-move', response_model=PlayMoveResponse)
async def play_move(request: PlayMoveRequest):
    try:
        # run search in thread pool to avoid blocking server event loop
        engine_response = await run_in_threadpool(
            game_service.play_move, 
            request.player_move, 
            request.session_id,
            request.client_fen
        )

        new_fen = engine_response[0]
        move_info = engine_response[1]

        return PlayMoveResponse(
            new_fen = new_fen,
            move_played = move_info['move'],
            depth_reached = move_info['depth'],
            nodes_searched = move_info['nodes'],
            is_book = move_info['is_book']
        )
    
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except RuntimeError as e:
        print(f"A server-side engine error occurred: {e}")
        raise HTTPException(status_code=500, detail='An internal engine error occurred')

    except Exception as e:
        print(f"An unexpected server error occurred: {e}")
        raise HTTPException(status_code=500, detail='An internal server error occurred')