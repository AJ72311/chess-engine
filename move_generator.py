import board
from board import Board, Move

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
    legal_moves = []        # initialize the final array of legal moves to return later
    board = position.board
    
    # define variables used in move generation logic
    if (position.color_to_play == 'white'):
        enemy_color = 'black'
        friendly_king = 'K'
        friendly_knight = 'N'
        friendly_bishop = 'B'
        friendly_rook = 'R'
        friendly_queen = 'Q'
        friendly_pawn = 'P'
        enemy_pawn = 'p'
        friendly_pieces = WHITE_PIECES
        enemy_pieces = BLACK_PIECES
        pawn_deltas = WHITE_PAWN_DELTAS
        promotion_squares = [21, 22, 23, 24, 25, 26, 27, 28]
        promotion_pieces = ['B', 'N', 'R', 'Q']
        castle_kingside = position.white_castle_kingside
        castle_queenside = position.white_castle_queenside
        kingside_castle_path = [96, 97]
        queenside_castle_path = [92, 93, 94]        # b1, c1, and d1 have to be empty
        queenside_king_castle_path = [93, 94]       # king path stops a c1
        castle_kingside_destination = 97
        castle_queenside_destination = 93
        king_home_square = 95
    else:
        enemy_color = 'white'
        friendly_king = 'k'
        friendly_knight = 'n'
        friendly_bishop = 'b'
        friendly_rook = 'r'
        friendly_queen = 'q'
        friendly_pawn = 'p'
        enemy_pawn = 'P'
        friendly_pieces = BLACK_PIECES
        enemy_pieces = WHITE_PIECES
        pawn_deltas = BLACK_PAWN_DELTAS
        promotion_squares = [91, 92, 93, 94, 95, 96, 97, 98]
        promotion_pieces = ['b', 'n', 'r', 'q']
        castle_kingside = position.black_castle_kingside
        castle_queenside = position.black_castle_queenside
        kingside_castle_path = [26, 27]
        queenside_castle_path = [22, 23, 24]       # b8, c8, and d8 have to be empty
        queenside_king_castle_path = [23, 24]      # king path stops at c8
        castle_kingside_destination = 27
        castle_queenside_destination = 23
        king_home_square = 25

    # get array of enemy-controlled squares and the number of checks in the position
    threat_map, check_count = get_threat_map(position, enemy_color)
    king_index = board.index(friendly_king)

    if check_count < 2:     # if not a double check
        checks, pins = get_checks_and_pins(position, king_index)    # arrays of check and pin dicts
        # structure of 'checks':
        # {
        #   'checker_index': ...,
        #   'check_path': [...],
        #   'is_sliding': ...
        # }

        # structure of 'pins':
        # {
        #   'pinner_index': ...,
        #   'pin_path': [...],
        #   'pinned_piece_index': ...
        # }

        is_check = False
        if len(checks) > 0:
            is_check = True
            check = checks[0]       # if is a check but len of checks array is < 2, there is only 1 element in checks

        for index, piece in enumerate(board):
            if piece in friendly_pieces:    # if this is a friendly-color piece
                # get pseudo-legal moves, each array includes all pseudo-legal destination squares                      
                if piece == friendly_knight:
                    pseudo_legal_moves = knight_moves(position, index)
                elif piece == friendly_bishop:
                    pseudo_legal_moves = bishop_moves(position, index)
                elif piece == friendly_rook:
                    pseudo_legal_moves = rook_moves(position, index)
                elif piece == friendly_queen:
                    pseudo_legal_moves = queen_moves(position, index)
                elif piece == friendly_king:
                    pseudo_legal_moves = king_moves(position, index)
                elif piece == friendly_pawn:
                    if (position.color_to_play == 'white'):
                        pawn_moves_dict = white_pawn_moves(position, index)
                    else:
                        pawn_moves_dict = black_pawn_moves(position, index)
                    
                    pseudo_legal_moves = pawn_moves_dict['attacks'] + pawn_moves_dict['advances']

                    # add en passant move if applicable
                    for delta in pawn_deltas['attacks']:
                        if index + delta == position.en_passant_square:
                            pseudo_legal_moves.append(index + delta)

                # VALIDATION STEP: loop through pseudo-legal moves
                for destination in pseudo_legal_moves:
                    if is_check:                                              # first round of filtering: checks
                        if piece != friendly_king:                            # if this is not a king
                            if not check['is_sliding']:                       # non-sliding checks must be captured
                                if destination != check['checker_index']:     # if move doesn't capture checker
                                    continue                                  # invalid move
                            else:                                             # sliding checks may be blocked or captured
                                if destination not in check['check_path']:    # if move doesn't block check
                                    if destination != check['checker_index']: # if move doesn't capture checker
                                        continue                              # invalid move

                    if piece == friendly_king:                                # second round of filtering: king moves
                        if destination in threat_map:                         # if square is attacked by enemy piece
                            continue                                          # invalid move
                    
                    is_pinned = False                                         # third round of filtering: pins
                    pin_info = None                                           # pin_info is a dict containing pin details
                    for pin in pins:                                      
                        if index == pin['pinned_piece_index']:                # if the current piece is pinned
                            is_pinned = True
                            pin_info = pin
                            break                                             # stop loop after identifying the pin
                    
                    if is_pinned:
                            if not (destination in pin_info['pin_path']):     # if the move leaves the pin's axis
                                if destination != pin_info['pinner_index']:   # if the move doesn't capture the pinner
                                    continue                                  # invalid move

                    if board[destination] in friendly_pieces:                 # fourth round of filtering: friendly pieces
                        continue                                              # can't land on square occupied by friend

                    # if all four rounds of filtering passed, the move is legal
                    if piece != friendly_pawn:                            # if this is not a pawn
                        # define arguments for legal Move object creation
                        moving_piece = piece
                        source_index = index
                        destination_index = destination
                        if (board[destination] in enemy_pieces):
                            piece_captured = board[destination]
                        else:
                            piece_captured = None
                        is_en_passant = False
                        is_castle = False
                        
                        # create legal Move object and append it to legal_moves
                        legal_move = Move(
                            position, moving_piece, source_index, destination_index,
                            piece_captured, is_en_passant, is_castle
                        )
                        legal_moves.append(legal_move)

                    elif piece == friendly_pawn:                          # if this is a pawn
                        if destination == position.en_passant_square:     # if this is an en passant move
                            # define arguments for new legal Move object creation
                            moving_piece = piece
                            source_index = index
                            destination_index = destination
                            piece_captured = enemy_pawn
                            is_en_passant = True
                            is_castle = False
                            
                            # create legal Move object and append it to legal moves
                            legal_move = Move(
                                position, moving_piece, source_index, destination_index,
                                piece_captured, is_en_passant, is_castle
                            )
                            legal_moves.append(legal_move)
                        elif destination in promotion_squares:            # if this is a promotion
                            for new_piece in promotion_pieces:            # for all promotion-eligible pieces
                                # define arguments for new legal Move object creation
                                moving_piece = piece
                                source_index = index
                                destination_index = destination
                                if (board[destination] in enemy_pieces):
                                    piece_captured = board[destination]
                                else:
                                    piece_captured = None
                                is_en_passant = is_castle = False
                                promotion_piece = new_piece

                                # create legal Move object and append it to legal_moves
                                legal_move = Move(
                                    position, moving_piece, source_index, destination_index,
                                    piece_captured, is_en_passant, is_castle, promotion_piece
                                )
                                legal_moves.append(legal_move)

                        else:                                             # if this is neither en passant nor a promotion
                            # define arguments for new legal Move object creation
                            moving_piece = piece
                            source_index = index
                            destination_index = destination
                            if (board[destination] in enemy_pieces):
                                piece_captured = board[destination]
                            else:
                                piece_captured = None
                            is_en_passant = is_castle = False
                        
                            # create legal Move object and append it to legal_moves
                            legal_move = Move(
                                position, moving_piece, source_index, destination_index,
                                piece_captured, is_en_passant, is_castle
                            )
                            legal_moves.append(legal_move)

        # manually generate castling moves:
        if castle_kingside:                                 # if kingside castling flag is True
            if not is_check:                                # cannot castle when in check
                castle_path_clear = True
                for index in kingside_castle_path:          # loop through f1 and g1 (white) / f8 and g8 (black)
                    if board[index] != EMPTY:               # if square is occupied
                        castle_path_clear = False           # cannot castle
                    if index in threat_map:                 # if square controlled by enemy piece
                        castle_path_clear = False           # cannot castle

                if castle_path_clear:
                    # define arguments for new legal Move object creation
                    moving_piece = friendly_king
                    source_index = king_home_square
                    destination_index = castle_kingside_destination
                    piece_captured = None
                    is_en_passant = False
                    is_castle = True

                    # create legal Move object and append it to legal_moves
                    legal_move = Move(
                        position, moving_piece, source_index, destination_index, 
                        piece_captured, is_en_passant, is_castle
                    )
                    legal_moves.append(legal_move)

        if castle_queenside:                                # if queenside castling flag is True
            if not is_check:                                # cannot castle when in check
                castle_path_clear = True
                for index in queenside_castle_path:         # loop through b1, c1, and d1 (white) / b8, c8, and d8 (black)
                    if board[index] != EMPTY:               # if square is ocupied
                        castle_path_clear = False           # cannot castle
                for index in queenside_king_castle_path:    # loop through c1 and d1 (white) / c8 and d8 (black)
                    if index in threat_map:                 # if square controlled by enemy piece
                        castle_path_clear = False           # cannot castle

                if castle_path_clear:
                    # define arguments for new legal Move object creation
                    moving_piece = friendly_king
                    source_index = king_home_square
                    destination_index = castle_queenside_destination
                    piece_captured = None
                    is_en_passant = False
                    is_castle = True
                    
                    # create legal Move object and append it to legal_moves
                    legal_move = Move(
                        position, moving_piece, source_index, destination_index, 
                        piece_captured, is_en_passant, is_castle
                    )
                    legal_moves.append(legal_move)

    elif check_count > 1:       # if double check, only king moves are valid
        pseudo_legal_moves = king_moves(position, king_index)       # get pseudo-legal moves for the king
        for destination in pseudo_legal_moves:
            if destination in threat_map:                           # first round of filtering: enemy-controlled squares
                continue
            if board[destination] in friendly_pieces:               # second round of filtering: friendly-occupied squares
                continue
        
            # if both rounds of filtering passed, move is valid
            # define arguments for new legal Move object creation
            moving_piece = friendly_king
            source_index = king_index
            destination_index = destination
            if (board[destination] in enemy_pieces):
                piece_captured = board[destination]
            else:
                piece_captured = None
            is_en_passant = is_castle = False

            # create legal Move object and append it to legal Moves
            legal_move = Move(
                position, moving_piece, source_index, destination_index, 
                piece_captured, is_en_passant, is_castle
            )
            legal_moves.append(legal_move)

    return legal_moves  # legal_moves now contains a Move object for all legal moves in this position

# helper function for generate_moves()
# returns an array of all enemy-controlled squares in a position
# additionally counts the number of checks found
def get_threat_map(position, enemy_color):
    check_count = 0     # used to detect if position has no checks, a single check, or a double check
    threat_map = []     # an array containing all enemy-controlled squares, used for king move generation
    board = position.board

    if enemy_color == 'white':
        enemy_pieces = WHITE_PIECES
        friendly_king = 'k'
        enemy_pawn_deltas = WHITE_PAWN_DELTAS
    else:
        enemy_pieces = BLACK_PIECES
        friendly_king = 'K'
        enemy_pawn_deltas = BLACK_PAWN_DELTAS

    for index, square in enumerate(board):
        if square in enemy_pieces:
            piece_type = square.lower()                         # convert all to lowercase to unify white / black logic

            # NON-SLIDING PIECES:
            if piece_type == 'n':                               # if enemy knight
                threat_map += knight_moves(position, index)     # add the knight's moves to the threat map
                continue
            elif piece_type == 'k':                             # if enemy king
                threat_map += king_moves(position, index)       # add the king's moves to the threat map
                continue

            # if enemy pawn, don't use helper funct, it doesn't include attacked empty squares    
            elif piece_type == 'p':
                for delta in enemy_pawn_deltas['attacks']:      # manually add pawn moves 
                    if board[index + delta] != OUT_OF_BOUNDS:
                        threat_map.append(index + delta)
                continue

            # SLIDING PIECES
            deltas = None
            if piece_type == 'b':       # if enemy bishop
                deltas = BISHOP_DELTAS
            if piece_type == 'r':       # if enemy rook
                deltas = ROOK_DELTAS
            if piece_type == 'q':       # if enemy queen
                deltas = QUEEN_DELTAS
            
            for direction in deltas:
                for delta in deltas[direction]:
                    target_index = index + delta
                    target_square = board[target_index]

                    if target_square == OUT_OF_BOUNDS:
                        break           # stop this direction's loop

                    threat_map.append(target_index)             # if not out of bounds, add to the threat map

                    # if this square is occupied by a piece other than friendly king, stop this direction's loop
                    # note: we don't stop at the friendly king to mark "x-ray" attacks
                    if (target_square != EMPTY) and (target_square != friendly_king):
                        break

    friendly_king_index = board.index(friendly_king)
    check_count = threat_map.count(friendly_king_index)         # how many times is our king attacked
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
                        pin_dict['pinner_index'] = current_index
                        pin_dict['pinned_piece_index'] = closest_friendly_piece_index
                        pin_dict['pin_path'] = pin_path + check_path
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

# generate pseudo-legal moves for black pawns, returns a dict with pseudo-legal attack and advance keys
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