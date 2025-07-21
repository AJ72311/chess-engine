import time
from board import Move, Board
from move_generator import generate_moves

# a mapping of the 10x12 board representation's indices into standard chess board coordinates
# used in the 'divide' function's ouput
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

# converts a move object into a simplified algebraic notation (eg. e2e4, e7e8q, etc.)
def move_to_algebraic(move):
    source_sq = INDEX_TO_ALGEBRAIC.get(move.source_index, '??')     # get the move's source index
    dest_sq = INDEX_TO_ALGEBRAIC.get(move.destination_index, '??')  # get the move's destination index

    promotion_char = ''                                               
    if move.promotion_piece:                            # if this move is a promotion
        promotion_char = move.promotion_piece.lower()   # set to lower case for consistency in white vs. black moves
    
    return f'{source_sq}{dest_sq}{promotion_char}'

# --- FEN AND BOARD STATE HELPERS ---
 
# generates a FEN string representation of the current board state
def board_to_fen(board):
    fen = ''
    for rank_start in range(21, 92, 10):
        empty_count = 0
        for i in range(rank_start, rank_start + 8):
            piece = board.board[i]
            if piece == '#':
                empty_count += 1
            else:
                if empty_count > 0:
                    fen += str(empty_count)
                    empty_count = 0
                fen += piece
        if empty_count > 0:
            fen += str(empty_count)
        if rank_start < 91:
            fen += '/'
    
    fen += f" {board.color_to_play[0]}"

    castling_rights = ""
    if board.white_castle_kingside: castling_rights += 'K'
    if board.white_castle_queenside: castling_rights += 'Q'
    if board.black_castle_kingside: castling_rights += 'k'
    if board.black_castle_queenside: castling_rights += 'q'
    fen += f" {castling_rights if castling_rights else '-'}"

    ep_square = '-'
    if board.en_passant_square:
        ep_square = INDEX_TO_ALGEBRAIC.get(board.en_passant_square, '-')
    fen += f" {ep_square}"
    
    fen += f" {board.half_move}"
    fen += f" {board.ply // 2 + 1}"
    
    return fen

# sets up a Board object from a FEN string
# note: this assumes a valid FEN
def set_board_from_fen(board, fen_string):
    parts = fen_string.split(' ')
    piece_placement = parts[0]
    
    new_board = list(board.board) # Start with a copy of the template
    board_index = 21
    for char in piece_placement:
        if char == '/':
            board_index += 2 # Go to the start of the next rank
        elif char.isdigit():
            for i in range(int(char)):
                new_board[board_index] = '#'
                board_index += 1
        else:
            new_board[board_index] = char
            board_index += 1
    board.board = new_board

    board.color_to_play = 'white' if parts[1] == 'w' else 'black'
    
    castling = parts[2]
    board.white_castle_kingside = 'K' in castling
    board.white_castle_queenside = 'Q' in castling
    board.black_castle_kingside = 'k' in castling
    board.black_castle_queenside = 'q' in castling

    ep_square = parts[3]
    board.en_passant_square = ALGEBRAIC_TO_INDEX.get(ep_square, None)

    board.half_move = int(parts[4])
    board.ply = (int(parts[5]) - 1) * 2
    if board.color_to_play == 'black':
        board.ply += 1

# recursively calcuates the number of leaf nodes at a given depth
def perft(board, depth):
    # base case, if depth is 0 we are at a leaf node, return 1 to count it
    if depth == 0:
        return 1
    
    nodes = 0                              # initialize nodes resulting from the current position's game tree
    legal_moves = generate_moves(board)

    for move in legal_moves:
        board.make_move(move)
        nodes += perft(board, depth - 1)   # recursive call, add total nodes resulting from move's game sub-tree to nodes
        board.unmake_move(move)

    return nodes

# runs a perft test to a set depth for each move possible in a given position
def divide(board, depth):
    if depth <= 0:  # depth has to be greater than 0
        print('Depth must be greater than 0 for a divide')
        return

    print(f'--- Divide for Depth {depth} ---')

    # log start time for speed perfomance testing
    start_time = time.time()

    total_nodes = 0
    legal_moves = generate_moves(board)

    # sort move list for consistent output, comparison against established results
    sorted_moves = sorted(legal_moves, key=lambda m: (m.source_index, m.destination_index))

    for move in sorted_moves:
        board.make_move(move)
        nodes = perft(board, depth - 1)
        total_nodes += nodes
        board.unmake_move(move)
        print(f'{move_to_algebraic(move)}: {nodes}')

    # log end time for speed performance testing
    end_time = time.time()
    elapsed_time = end_time - start_time
    nodes_per_second = total_nodes / elapsed_time if elapsed_time > 0 else 0

    print('\n--- Summary ---')
    print(f'Total Moves: {len(legal_moves)}')
    print(f'Total Nodes: {total_nodes}')
    print(f'Elapsed Time: {elapsed_time:.4f} seconds')
    print(f'Nodes per Second: {nodes_per_second:,.2f}')

if __name__ == '__main__':
    TEST_DEPTH = 5              # depth to search during tests
    test_board = Board()        # create a Board object for testing, represents the starting position

    FEN_STRING = ''

    if FEN_STRING:
        set_board_from_fen(test_board, FEN_STRING)

    divide(test_board, TEST_DEPTH)  # run the test