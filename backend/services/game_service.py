from board import Board
from engine import Search
from utils import set_board_from_fen, board_to_fen, move_to_algebraic
import time

def new_game(input_fen: str):
    board = Board()
    set_board_from_fen(board, input_fen)
    search = Search(depth=64)

    engine_color = board.color_to_play
    max_think_time = 6

    print(f'Engine ({engine_color}) is thinking...')

    start_time = time.time()  # log time for performance testing
    engine_move = search.find_best_move(board, engine_color, max_think_time)  # find the best move
    end_time = time.time()    # log end time

    print(f'Engine found move in {end_time - start_time:.2f} seconds.')
    print(f'Engine move: {move_to_algebraic(engine_move)}')
    
    board.make_move(engine_move)
    return board_to_fen(board)