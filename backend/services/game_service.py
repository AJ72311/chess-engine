from board import Board
from engine import Search
from move_generator import generate_moves
from utils import board_to_fen, move_to_algebraic, parse_user_move
import uuid
import time
import traceback

# --- constants ---
ENGINE_THINK_TIME = 6   # engine think time capped at 6 seconds
SESSION_TIMEOUT = 900   # 15 minutes

def run_worker(task_queue, result_dict):    
    """
    The main loop for a worker process.

    Args:
        task_queue (multiprocessing.Queue): the queue to receive tasks from
        results_dict (multiprocessing.Dict): shared dict to put results in
    """

    # worker's private memory, mapping a Board and Search instance to each assigned session
    active_sessions = {}
    print('Chess worker process started')

    while True:
        try:
            # blocking call, worker sleeps here until a task arrives
            task_id, command, kwargs = task_queue.get()

            # --- new_game task ---
            if command == 'new_game':
                _prune_inactive_sessions(active_sessions)

                result = _new_game(active_sessions, **kwargs)
                result_dict[task_id] = ('ok', result)

            # --- play_move task ---
            elif command == 'play_move':
                result = _play_move(active_sessions, **kwargs)
                result_dict[task_id] = ('ok', result)

            # --- prune_sessions task
            elif command == 'prune_sessions':
                sessions_before = len(active_sessions)
                _prune_inactive_sessions(active_sessions)
                sessions_after = len(active_sessions)

                pruned_count = sessions_before - sessions_after
                result_dict[task_id] = ('ok', pruned_count)

            # --- prune_single_session task ---
            elif command == 'prune_single_session':
                target_id = kwargs.get('session_id')
                if target_id in active_sessions:
                    print(f'Pruning session {target_id} due to client unload')
                    del active_sessions[target_id]

            else:
                result_dict[task_id] = ('error', 'Unknown command')
        
        except Exception as e:
            # safety net, prevents dispatcher from waiting forever for a response
            print(f'An error occurred in a worker process: {e}')
            traceback.print_exc()

            # check if task_id was defined before writing to result_dict
            if 'task_id' in locals():
                result_dict[task_id] = ('error', str(e))

def _prune_inactive_sessions(active_sessions):
    """Iterates through active_sessions and prunes any sessions that have timed out."""

    current_time = time.time()

    # get all uuids corresponding to timed-out sessions
    timed_out_sessions = [
        game_id for game_id, session in active_sessions.items()
        if (current_time - session['last_activity']) > SESSION_TIMEOUT
    ]

    # prune all timed-out uuids
    for game_id in timed_out_sessions:
        print(f'Pruning inactive session: {game_id}')
        del active_sessions[game_id]

def _new_game(active_sessions, player_move: str | None):
    """Creates a new active session and initializes the Board and Search instances."""

    board = Board()
    search = Search(depth=64)
    game_id = str(uuid.uuid4())
    
    # create a new game in sessions dict
    active_sessions[game_id] = {
        'search': search,
        'board': board,
        'last_activity': time.time(),
    }

    # if applicable, make the player's move first
    if player_move:
        _make_player_move(board, player_move)

    # computer's turn
    move_info = _play_engine_turn(board, search, ENGINE_THINK_TIME)

    active_sessions[game_id]['last_activity'] = time.time()
    
    # return the session id, along with the computer's move information and new FEN
    return (
        board_to_fen(board),
        move_info,
        game_id,
    )

def _play_move(active_sessions, player_move: str, session_id: str, client_fen: str):
    """Receives player's move from frontend, plays it, and returns FEN with response."""

    board = None
    search = None

    # get this session's board and search instances
    session_data = active_sessions.get(session_id)
    if not session_data:
        raise KeyError('Invalid or expired session ID')
    
    board = session_data['board']
    search = session_data['search']

    # ensure the client's FEN is the same as the server's
    server_fen = board_to_fen(board)
    if (server_fen != client_fen):
        raise ValueError('Client board is out of sync')
    
    # make the player's move
    _make_player_move(board, player_move)

    # play the engine's response
    move_info = _play_engine_turn(board, search, ENGINE_THINK_TIME)
    new_fen = board_to_fen(board)

    session_data['last_activity'] = time.time()

    # return the updated FEN and move information
    return (
        new_fen, 
        move_info,
    )

def _make_player_move(board, player_move):
    legal_moves, _ = generate_moves(board)
    move_to_make = parse_user_move(player_move, legal_moves)

    if move_to_make:
        board.make_move(move_to_make)
    else:
        raise ValueError('User-provided move is invalid')
    
def _play_engine_turn(board, search, max_think_time):
    engine_color = board.color_to_play
    print(f'Engine ({engine_color}) is thinking...')

    start_time = time.time()  # log time for performance testing
    engine_response = search.find_best_move(board, engine_color, max_think_time)
    end_time = time.time()    # log end time

    engine_move = engine_response['move']
    depth_reached = engine_response['depth']
    nodes_searched = engine_response['nodes']
    is_book = engine_response['is_book']

    if not engine_move:
        raise RuntimeError('Engine failed to find a move')

    print(f'Engine found move in {end_time - start_time:.2f} seconds.')
    print(f'Engine move: {move_to_algebraic(engine_move)}')
    
    board.make_move(engine_move)

    return {
        'move': move_to_algebraic(engine_move), 
        'depth': depth_reached, 
        'nodes': nodes_searched, 
        'is_book': is_book,
    }