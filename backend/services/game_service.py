from board import Board
from engine import Search
from move_generator import generate_moves
from utils import board_to_fen, move_to_algebraic, parse_user_move, set_board_from_fen
import uuid
import time

active_sessions = {}    # store a Board and Seach instance for each on-going game, indexed by a uuid
ENGINE_THINK_TIME = 6   # engine think time capped at 6 seconds

# creates a new active session and initializes the Board and Search instances
def new_game(player_move: str | None):
    board = Board()
    set_board_from_fen(board, '8/4ppkp/6p1/8/8/7p/1r6/5Kr1 w - - 0 1')
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
    move_info = _play_engine_turn(board, search, ENGINE_THINK_TIME)
    
    # return the session id, along with the computer's move information and new FEN
    return (
        board_to_fen(board),
        move_info,
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
    move_info = _play_engine_turn(board, search, ENGINE_THINK_TIME)
    new_fen = board_to_fen(board)

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