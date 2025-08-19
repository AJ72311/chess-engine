from board import Board
from engine import Search
from move_generator import generate_moves
from utils import board_to_fen, move_to_algebraic, parse_user_move
import uuid
import time

active_sessions = {}    # store a Board and Seach instance for each on-going game, indexed by a uuid
ENGINE_THINK_TIME = 6   # engine think time capped at 6 seconds

# creates a new active session and initializes the Board and Search instances
def new_game(player_move: str | None):
    board = Board()
    search = Search(depth=64)
    game_id = str(uuid.uuid4())

    # store new game in active sessions
    active_sessions[game_id] = {
        'search': search,
        'board': board,
    }

    # if applicable, make the player's move first
    if player_move:
        _make_player_move(board, player_move)

    # computer's turn
    _play_engine_turn(board, search, ENGINE_THINK_TIME)
    
    return (
        board_to_fen(board),
        game_id,
    )

# receives player's move from frontned, plays it, and returns FEN with response
def play_move(player_move: str, session_id: str, client_fen: str):
    # get this session's board and search instances
    session_data = active_sessions.get(session_id)
    
    if not session_data:
        raise KeyError('Invalid session ID')
    
    board = session_data['board']
    search = session_data['search']

    # ensure the client's FEN is the same as the server's
    server_fen = board_to_fen(board)
    if (server_fen != client_fen):
        raise ValueError('Client board is out of sync')
    

    # make the player's move
    _make_player_move(board, player_move)

    # play the engine's response
    _play_engine_turn(board, search, ENGINE_THINK_TIME)

    # return the updated FEN
    return board_to_fen(board)

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
    engine_move = search.find_best_move(board, engine_color, max_think_time)
    end_time = time.time()    # log end time

    if not engine_move:
        raise RuntimeError('Engine failed to find a move')

    print(f'Engine found move in {end_time - start_time:.2f} seconds.')
    print(f'Engine move: {move_to_algebraic(engine_move)}')
    
    board.make_move(engine_move)