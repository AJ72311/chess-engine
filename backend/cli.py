from engine import Search
from board import Board, Move
from move_generator import generate_moves
import time

# HELPER FUNCTIONS FOR THE GAME LOOP
# a mapping from 10x12 indices to standard algebraic notation.
from utils import INDEX_TO_ALGEBRAIC, ALGEBRAIC_TO_INDEX, parse_user_move, move_to_algebraic

# prints the board to the console in a human-readable format
def print_board(position):
    board_array = position.board
    print('\n   a b c d e f g h')
    print("  +-----------------+")

    # loop through rows
    for rank in range(8):
        rank_index = 8 - rank
        line = f"{rank_index} | "               # the string for this rank that will be printed

        # loop through columns
        for file in range(8):
            sq_index = 21 + (rank * 10) + file  # index 21 represents the first square on the board (a8)
            piece = board_array[sq_index]       # get the piece on this square
            line += f'{piece} '                 # add the piece's symbol to the string

        line += f'| {rank_index}'               # add the rank index to the string
        print(line)                             # print the current rank
    
    print("  +-----------------+")
    print("   a b c d e f g h\n")

# MAIN GAME LOOP
def play_game(human_color='white', max_think_time=6):
    board = Board()
    search = Search(depth=64)
    engine_color = 'black' if human_color == 'white' else 'white'

    while True:
        print_board(board)

        # generate all legal moves and count the number of checks
        legal_moves, check_count = generate_moves(board)

        # check if game over
        if not legal_moves:
            if check_count > 0:
                print('Checkmate!')
                winner = 'black' if board.color_to_play == 'white' else 'white'
                print(f'{winner} wins!')
            else:
                print('Stalemate! The game is a draw.')
            break

        # player's turn
        if board.color_to_play == human_color:
            move_to_make = None
            while move_to_make is None:
                user_input = input('Enter your move (e.g. e2e4): ')
                move_to_make = parse_user_move(user_input, legal_moves)

                if move_to_make is None:
                    print('Invalid or illegal move. Please try again.')
                
            print(f'Your move: {move_to_algebraic(move_to_make)}')
            board.make_move(move_to_make)

        # engine's turn
        else:
            print(f'Engine ({engine_color}) is thinking...')
            start_time = time.time()  # log time for performance testing
            engine_move = search.find_best_move(board, engine_color, max_think_time)  # find the best move
            end_time = time.time()    # log end time

            print(f'Engine found move in {end_time - start_time:.2f} seconds.')

            if engine_move:
                print(f'Engine move: {move_to_algebraic(engine_move)}')
                board.make_move(engine_move)
            else:   # if for some reason engine couldn't find a move, print error message
                print('Engine found no move, but game is not over... This is a bug.')
                break

if __name__ == '__main__':
    # CONFIGURE SETTINGS
    HUMAN_PLAYER_COLOR = 'white'       # change to 'black' to play as black
    ENGINE_THINKING_TIME = 6           # iterative deepening time limit (in seconds)

    # START GAME
    play_game(HUMAN_PLAYER_COLOR, ENGINE_THINKING_TIME)