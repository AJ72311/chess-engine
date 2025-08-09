# utility functions used to setup a game or read the opening book

# used to convert the 120-length position.board index to a 64-square index for Zobrist hash calculations
TO_64 = [
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1,  0,  1,  2,  3,  4,  5,  6,  7, -1,
    -1,  8,  9, 10, 11, 12, 13, 14, 15, -1,
    -1, 16, 17, 18, 19, 20, 21, 22, 23, -1,
    -1, 24, 25, 26, 27, 28, 29, 30, 31, -1,
    -1, 32, 33, 34, 35, 36, 37, 38, 39, -1,
    -1, 40, 41, 42, 43, 44, 45, 46, 47, -1,
    -1, 48, 49, 50, 51, 52, 53, 54, 55, -1,
    -1, 56, 57, 58, 59, 60, 61, 62, 63, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1
]

# a mapping of the 10x12 board representation's indices into standard chess board coordinates
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
    source_sq = INDEX_TO_ALGEBRAIC.get(move.source_index, '??')
    dest_sq = INDEX_TO_ALGEBRAIC.get(move.destination_index, '??')

    promotion_char = ''                                               
    if move.promotion_piece:
        promotion_char = move.promotion_piece.lower()
    
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
    if len(parts) != 6:
        print(f"Error: Invalid FEN string. Expected 6 fields, but got {len(parts)}.")
        return

    piece_placement = parts[0]
    
    new_board = list(board.board)
    board_index = 21
    for char in piece_placement:
        if char == '/':
            board_index += 2
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

    # 1. Clear the old piece lists from the starting position
    for piece in board.piece_lists:
        board.piece_lists[piece].clear()
    
    # 2. Re-populate the piece lists based on the new board state
    board.initialize_piece_lists()

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