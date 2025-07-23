from engine import find_best_move
from board import Board, Move
from move_generator import generate_moves
import time

# HELPER FUNCTIONS FOR THE GAME LOOP
# a mapping from 10x12 indices to standard algebraic notation.
INDEX_TO_ALGEBRAIC = {
    21: 'a8', 22: 'b8', 23: 'c8', 24: 'd8', 25: 'e8', 26: 'f8', 27: 'g8', 28: 'h8',
    31: 'a7', 32: 'b7', 33: 'c7', 34: 'd7', 35: 'e7', 36: 'f7', 37: 'g7', 38: 'h7',
    41: 'a6', 42: 'b6', 43: 'c6', 44: 'd6', 45: 'e6', 46: 'f6', 47: 'g6', 48: 'h6',
    51: 'a5', 52: 'b5', 53: 'c5', 54: 'd5', 55: 'e5', 56: 'f5', 57: 'g5', 58: 'h5',
    61: 'a4', 62: 'b4', 63: 'c4', 64: 'd4', 65: 'e4', 66: 'f4', 67: 'g4', 68: 'h4',
    71: 'a3', 72: 'b3', 73: 'c3', 74: 'd3', 75: 'e3', 76: 'f3', 77: 'g3', 78: 'h3',
    81: 'a2', 82: 'b2', 83: 'c2', 84: 'd2', 85: 'e2', 86: 'f2', 87: 'g2', 88: 'h2',
    91: 'a1', 92: 'b1', 93: 'c1', 94: 'd1', 95: 'e1', 96: 'f1', 97: 'g1', 98: 'h1',
}
ALGEBRAIC_TO_INDEX = {v: k for k, v in INDEX_TO_ALGEBRAIC.items()}

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

# converts a Move object to simplified algebraic notation for printing
def move_to_algebraic(move):
    source_sq = INDEX_TO_ALGEBRAIC.get(move.source_index, '??') 
    dest_sq = INDEX_TO_ALGEBRAIC.get(move.destination_index, '??')
    promo_char = move.promotion_piece.lower() if move.promotion_piece else ''   # for promotions only
    return f"{source_sq}{dest_sq}{promo_char}"

# parses the user's input (eg. e2e4) and finds the corresponding legal Move object
# returns the Move object if found, otherwise None
def parse_user_move(input_str, legal_moves):
    if len(input_str) < 4:
        return None
    
    source_str = input_str[0:2]
    dest_str = input_str[2:4]
    promo_char = input_str[4] if len(input_str) > 4 else None

    source_index = ALGEBRAIC_TO_INDEX.get(source_str)
    dest_index = ALGEBRAIC_TO_INDEX.get(dest_str)

    if source_index is None or dest_index is None:
        return None
    
    # find the matching legal move
    for move in legal_moves:
        if move.source_index == source_index and move.destination_index == dest_index:
            # if promotion, ensure promotion piece matches
            if move.promotion_piece:
                if (promo_char) and (move.promotion_piece.lower() == promo_char):
                    return move
            else:
                return move
            
    # if no legal move found
    return None

# MAIN GAME LOOP
def play_game(human_color='white'):
    board = Board()
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
            start_time = time.time()                            # log time for performance testing
            engine_move = find_best_move(board, engine_color)   # find the best move
            end_time = time.time()                              # log end time

            print(f'Engine found move in {end_time - start_time:.2f} seconds.')

            if engine_move:
                print(f'Engine move: {move_to_algebraic(engine_move)}')
                board.make_move(engine_move)
            else:   # if for some reason engine couldn't find a move, print error message
                print('Engine found no move, but game is not over? This is a bug.')
                break

if __name__ == '__main__':
    # CONFIGURE SETTINGS
    HUMAN_PLAYER_COLOR = 'white'       # change to 'black' to play as black

    # START GAME
    play_game(HUMAN_PLAYER_COLOR)