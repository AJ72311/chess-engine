import board

# global empty square and out-of-bounds square constants
EMPTY = '#'
OUT_OF_BOUNDS = -1

# global piece code constants
WHITE_PIECES = ['K', 'Q', 'R', 'B', 'N', 'P']
BLACK_PIECES = ['k', 'q', 'r', 'b', 'n', 'p']

# global piece delta constants
KING_DELTAS = [1, -1, 10, -10, 9, -9, 11, -11]
KNIGHT_DELTAS = [8, 12, 19, 21, -8, -12, -19, -21]
ROOK_DELTAS = {
    'up': [-10, -20, -30, -40, -50, -60, -70],
    'down': [10, 20, 30, 40, 50, 60, 70],
    'right': [1, 2, 3, 4, 5, 6, 7],
    'left': [-1, -2, -3, -4, -5, -6, -7],
}
BISHOP_DELTAS = {
    'up-right': [-9, -18, -27, -36, -45, -54, -63],
    'up-left': [-11, -22, -33, -44, -55, -66, -77],
    'down-right': [11, 22, 33, 44, 55, 66, 77],
    'down-left': [9, 18, 27, 36, 45, 54, 63]
}
QUEEN_DELTAS = ROOK_DELTAS | BISHOP_DELTAS
WHITE_PAWN_DELTAS = {
    'attacks': [-9, -11], 
    'advances': [-10, -20]
}
BLACK_PAWN_DELTAS = {
    'attacks': [9, 11], 
    'advances': [10, 20]
}

# generates all legal moves for a position, "position" is a "Board" object
def generate_moves(position):
    pass

# helper function for generate_moves()
# returns an array of all enemy-controlled squares in a position
# additionally counts the number of checks found and returns an array of dicts for non-sliding piece checks
def get_enemy_attacks(position):
    pass

# helper function for generate_moves()
# casts rays from the king's index to all 8 directions to find checks, pins, and their corresponding paths
# returns an array of check dicts, and an array of pin dicts
def get_checks_and_pins(position): 
    pass

# generate pseudo-legal target squares for non-sliding pieces, returns an array of all non-out-of-bounds squares
def non_sliding_moves(position, source_index, deltas):   # used by kings and knights
    destinations = []

    for delta in deltas:
        target_index = source_index + delta
        target_square = position.board[target_index]

        if target_square != OUT_OF_BOUNDS:
            destinations.append(target_index)

    return destinations

# generate pseudo-legal target squares for sliding pieces, returns an array of all non-out-of-bounds squares
def sliding_moves(position, source_index, deltas):      # used by bishops, rooks, and queens
    destinations = []

    for direction in deltas:
        for delta in deltas[direction]:
            target_index = source_index + delta
            target_square = position.board[target_index]

            if target_square == OUT_OF_BOUNDS:
                break

            destinations.append(target_index)

            if target_square != EMPTY:                  # if the square we just appended was a piece, stop the loop
                break
    
    return destinations

def king_moves(position, source_index):     # wrapper function for non_sliding_moves(), castling handled in generate_moves()
    return non_sliding_moves(position, source_index, KING_DELTAS)

def knight_moves(position, source_index):   # wrapper function for non_sliding_moves()
    return non_sliding_moves(position, source_index, KNIGHT_DELTAS)

def rook_moves(position, source_index):     # wrapper function for sliding_moves()
    return sliding_moves(position, source_index, ROOK_DELTAS)

def bishop_moves(position, source_index):   # wrapper function for sliding_moves()
    return sliding_moves(position, source_index, BISHOP_DELTAS)

def queen_moves(position, source_index):    # wrapper function for sliding_moves()
    return sliding_moves(position, source_index, QUEEN_DELTAS)

# generate pseudo-legal moves for white pawns, returns an dict with pseudo-legal attack and advance keys
def white_pawn_moves(position, source_index):   # en passant and promotion will be handled in generate_moves()
    destinations = {
        'attacks': [],
        'advances': []
    }

    for delta in WHITE_PAWN_DELTAS['advances']:
        target_index = source_index + delta
        target_square = position.board[target_index]

        if target_square != EMPTY:
            break # stop looping if path is blocked

        destinations['advances'].append(target_index)

        if not (source_index >= 81 and source_index <= 88): # if the pawn is not on the home square, break after first advance
            break   # pawns can only advance two squares if they are on the home square

    for delta in WHITE_PAWN_DELTAS['attacks']:
        target_index = source_index + delta
        target_square = position.board[target_index]

        if target_square in BLACK_PIECES: # if square is an enemy piece
            destinations['attacks'].append(target_index)

    return destinations

# generate pseudo-legal moves for black pawns, returns an dict with pseudo-legal attack and advance keys
def black_pawn_moves(position, source_index):   # en passant and promotion will be handled in generate_moves()
    destinations = {
        'attacks': [],
        'advances': []
    }

    for delta in BLACK_PAWN_DELTAS['advances']:
        target_index = source_index + delta
        target_square = position.board[target_index]

        if target_square != EMPTY:
            break # stop looping if path is blocked

        destinations['advances'].append(target_index)

        if not (source_index >= 31 and source_index <= 38): # if the pawn is not on the home square, break after first advance
            break   # pawns can only advance two squares if they are on the home square

    for delta in BLACK_PAWN_DELTAS['attacks']:
        target_index = source_index + delta
        target_square = position.board[target_index]

        if target_square in WHITE_PIECES: # if square is an enemy piece
            destinations['attacks'].append(target_index)

    return destinations