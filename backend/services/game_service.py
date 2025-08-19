from board import Board
from engine import Search
from move_generator import generate_moves
from utils import board_to_fen, move_to_algebraic, parse_user_move
import uuid
import time

active_sessions = {} # store a Seach instance for each on-going game, indexed by a uuid

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
    _play_engine_turn(board, search, 6) # max think time of 6 seconds
    
    return (
        board_to_fen(board),
        game_id,
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
    engine_move = search.find_best_move(board, engine_color, max_think_time)
    end_time = time.time()    # log end time

    if not engine_move:
        raise RuntimeError('Engine failed to find a move')

    print(f'Engine found move in {end_time - start_time:.2f} seconds.')
    print(f'Engine move: {move_to_algebraic(engine_move)}')
    
    board.make_move(engine_move)