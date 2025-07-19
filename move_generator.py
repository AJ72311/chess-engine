import board

# global empty square and out-of-bounds square constants
EMPTY = '#'
OUT_OF_BOUNDS = -1

# global piece code constants
WHITE_PIECES = ['K', 'Q', 'R', 'B', 'N', 'P']
BLACK_PIECES = ['k', 'q', 'r', 'b', 'n', 'p']

# direction deltas
DIRECTION_DELTAS = {
    'N': -10, 'S': 10, 'E': 1, 'W': -1,
    'NE': -9, 'NW': -11, 'SE': 11, 'SW': 9
}

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
# additionally counts the number of checks found
def get_threat_map(position, enemy_color):
    check_count = 0     # used to detect if position has no checks, a single check, or a double check
    threat_map = []     # an array containing all enemy-controlled squares, used for king move generation
    board = position.board

    if enemy_color == 'white':
        for index, square in enumerate(board):
            if square == 'B':       # if white bishop
                threat_map += bishop_moves(position, index)    # add the bishop's moves to the threat map
            elif square == 'R':     # if white rook
                threat_map += rook_moves(position, index)      # add the rook's moves to the threat map
            elif square == 'Q':     # if white queen
                threat_map += queen_moves(position, index)     # add the queen's moves to the threat map
            elif square == 'N':     # if white knight
                threat_map += knight_moves(position, index)    # add the knight's moves to the threat map
            elif square == 'K':     # if white king
                threat_map += king_moves(position, index)      # add the king's moves to the threat map
            elif square == 'P':     # if white pawn
                threat_map += white_pawn_moves(position, index)['attacks'] # add the pawn's moves to the threat map

        black_king_index = board.index('k')
        check_count = threat_map.count(black_king_index)    # used to detect double checks

    elif enemy_color == 'black':
        for index, square in enumerate(board):
            if square == 'b':       # if black bishop
                threat_map += bishop_moves(position, index)    # add the bishop's moves to the threat map
            elif square == 'r':     # if black rook
                threat_map += rook_moves(position, index)      # add the rook's moves to the threat map
            elif square == 'q':     # if black queen
                threat_map += queen_moves(position, index)     # add the queen's moves to the threat map
            elif square == 'n':     # if black knight
                threat_map += knight_moves(position, index)    # add the knight's moves to the threat map
            elif square == 'k':     # if black king
                threat_map += king_moves(position, index)      # add the king's moves to the threat map
            elif square == 'p':     # if black pawn
                threat_map += black_pawn_moves(position, index)['attacks'] # add the pawn's moves to the threat map
        
        white_king_index = board.index('K')
        check_count = threat_map.count(white_king_index)    # used to detect double checks

    return threat_map, check_count

# helper function for generate_moves()
# casts rays from the king's index to all 8 directions to find checks, pins, and their corresponding paths
# returns an array of check dicts, and an array of pin dicts
def get_checks_and_pins(position, source_index): 
    board = position.board
    checks = [] # contains dicts of this position's checks
    pins = []   # contains dicts of this position's pins

    # define friendly/enemy piece constants for white and black
    if position.color_to_play == 'white':
        friendly_pieces = WHITE_PIECES
        enemy_pieces = BLACK_PIECES
        enemy_orthogonal = ['r', 'q']
        enemy_diagonal = ['b', 'q']
        enemy_pawn = 'p'
        enemy_knight = 'n'
        pawn_deltas = WHITE_PAWN_DELTAS['attacks']
    else:
        friendly_pieces = BLACK_PIECES
        enemy_pieces = WHITE_PIECES
        enemy_orthogonal = ['R', 'Q']
        enemy_diagonal = ['B', 'Q']
        enemy_pawn = 'P'
        enemy_knight = 'N'
        pawn_deltas = BLACK_PAWN_DELTAS['attacks']

    for direction, delta in DIRECTION_DELTAS.items():   # loop to detect pins and sliding checks
        friendly_pieces_in_ray = 0                      # for differentiating checks and pins
        closest_friendly_piece_index = None             # for tracking pinned piece index
        pin_found = False
        check_found = False
        pin_path = []                                   # contains all indices btwn pinning and pinned pieces
        check_path = []                                 # contains all indices btwn checking and checked pieces
        pin_dict = {}                                   # logs information about the pin (if any)
        check_dict = {}                                 # logs information about the check (if any)

        current_index = source_index                    # tracks how far along a ray we currently are
        while board[current_index] != OUT_OF_BOUNDS:
            current_index += delta                      # increment by current direction's delta
            encountered_square = board[current_index]

            if encountered_square in friendly_pieces:
                friendly_pieces_in_ray += 1             
                if friendly_pieces_in_ray == 1:         # if only one friendly piece in path so far
                    closest_friendly_piece_index = current_index
                elif friendly_pieces_in_ray == 2:       # if two friendly pieces found along ray
                    break                               # no pins or checks on this ray, exit loop

            elif encountered_square == EMPTY:
                if friendly_pieces_in_ray == 1:         # if one friendly piece in ray, potential pin path square
                    pin_path.append(current_index)
                elif friendly_pieces_in_ray == 0:       # if no friendly piece in ray, potential check path square
                    check_path.append(current_index)

            elif encountered_square in enemy_pieces:
                # only rooks and queens for horizontal/vertical checks, only bishops/queens for diagonal checks
                if ((direction in ['N', 'S', 'E', 'W'] and encountered_square in enemy_orthogonal)
                or (direction in ['NW', 'NE', 'SW', 'SE'] and encountered_square in enemy_diagonal)):
                    if friendly_pieces_in_ray == 0:     # no friendly pieces along ray, it's a check
                        check_found = True
                        check_dict['checker_index'] = current_index
                        check_dict['check_path'] = check_path
                        check_dict['is_sliding'] = True
                        break
                    elif friendly_pieces_in_ray == 1:   # 1 friendly piece along ray, it's a pin
                        pin_found = True
                        pin_dict['pinned_piece_index'] = closest_friendly_piece_index
                        pin_dict['pin_path'] = pin_path
                        break
                else:
                    break   # no pins or checks, exit loop
            
        # after while loop ends
        if pin_found:
            pins.append(pin_dict)
        if check_found:
            checks.append(check_dict)
        
    # after ray casting loop ends, manually search for pawn and knight checks
    for delta in KNIGHT_DELTAS:
        if board[source_index + delta] == enemy_knight:
            checks.append({
                'checker_index': source_index + delta,
                'check_path': None,
                'is_sliding': False
            })
    for delta in pawn_deltas: # use friendly pawn deltas to determine if king is in enemy pawn attack range
        if board[source_index + delta] == enemy_pawn:
            checks.append({
                'checker_index': source_index + delta,
                'check_path': None,
                'is_sliding': False
            })

    return checks, pins


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