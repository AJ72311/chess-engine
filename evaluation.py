from board import Board, Move
from board import TO_64  # used to convert the 120-length position.board index to a 64-square index for PSTs
from move_generator import KING_DELTAS, QUEEN_DELTAS, ROOK_DELTAS, BISHOP_DELTAS, KNIGHT_DELTAS, OUT_OF_BOUNDS, EMPTY

# DATA STRUCTURES
# a lookup table to find the vertically mirrored square index-based
# used to correctly apply white-oriented PSTs to black piece_lists
FLIP = [
      0,   1,   2,   3,   4,   5,   6,   7,   8,   9,
     10,  11,  12,  13,  14,  15,  16,  17,  18,  19,
     20,  91,  92,  93,  94,  95,  96,  97,  98,  29,
     30,  81,  82,  83,  84,  85,  86,  87,  88,  39,
     40,  71,  72,  73,  74,  75,  76,  77,  78,  49,
     50,  61,  62,  63,  64,  65,  66,  67,  68,  59,
     60,  51,  52,  53,  54,  55,  56,  57,  58,  69,
     70,  41,  42,  43,  44,  45,  46,  47,  48,  79,
     80,  31,  32,  33,  34,  35,  36,  37,  38,  89,
     90,  21,  22,  23,  24,  25,  26,  27,  28,  99,
    100, 101, 102, 103, 104, 105, 106, 107, 108, 109,
    110, 111, 112, 113, 114, 115, 116, 117, 118, 119
]

# PIECE SQUARE TABLES (PST), index-based scores used to modify material evaluation
# all tables are from white's perspectve
# values from PeSTO's evaluation function
# mg = mid-game and eg = end-game, use interpolated game_phase value for weights
MG_PAWN_PST = [
     0,    0,   0,   0,   0,   0,  0,   0,
     98, 134,  61,  95,  68, 126, 34, -11,
     -6,   7,  26,  31,  65,  56, 25, -20,
    -14,  13,   6,  21,  23,  12, 17, -23,
    -27,  -2,  -5,  12,  17,   6, 10, -25,
    -26,  -4,  -4, -10,   3,   3, 33, -12,
    -35,  -1, -20, -23, -15,  24, 38, -22,
      0,   0,   0,   0,   0,   0,  0,   0,  
]

EG_PAWN_PST = [
      0,   0,   0,   0,   0,   0,   0,   0,
    178, 173, 158, 134, 147, 132, 165, 187,
     94, 100,  85,  67,  56,  53,  82,  84,
     32,  24,  13,   5,  -2,   4,  17,  17,
     13,   9,  -3,  -7,  -7,  -8,   3,  -1,
      4,   7,  -6,   1,   0,  -5,  -1,  -8,
     13,   8,   8,  10,  13,   0,   2,  -7,
      0,   0,   0,   0,   0,   0,   0,   0,
]

MG_KNIGHT_PST = [
    -167, -89, -34, -49,  61, -97, -15, -107,
     -73, -41,  72,  36,  23,  62,   7,  -17,
     -47,  60,  37,  65,  84, 129,  73,   44,
      -9,  17,  19,  53,  37,  69,  18,   22,
     -13,   4,  16,  13,  28,  19,  21,   -8,
     -23,  -9,  12,  10,  19,  17,  25,  -16,
     -29, -53, -12,  -3,  -1,  18, -14,  -19,
    -105, -21, -58, -33, -17, -28, -19,  -23,
]

EG_KNIGHT_PST = [
    -58, -38, -13, -28, -31, -27, -63, -99,
    -25,  -8, -25,  -2,  -9, -25, -24, -52,
    -24, -20,  10,   9,  -1,  -9, -19, -41,
    -17,   3,  22,  22,  22,  11,   8, -18,
    -18,  -6,  16,  25,  16,  17,   4, -18,
    -23,  -3,  -1,  15,  10,  -3, -20, -22,
    -42, -20, -10,  -5,  -2, -20, -23, -44,
    -29, -51, -23, -15, -22, -18, -50, -64,
]

MG_BISHOP_PST = [
    -29,   4, -82, -37, -25, -42,   7,  -8,
    -26,  16, -18, -13,  30,  59,  18, -47,
    -16,  37,  43,  40,  35,  50,  37,  -2,
     -4,   5,  19,  50,  37,  37,   7,  -2,
     -6,  13,  13,  26,  34,  12,  10,   4,
      0,  15,  15,  15,  14,  27,  18,  10,
      4,  15,  16,   0,   7,  21,  33,   1,
    -33,  -3, -14, -21, -13, -12, -39, -21,
]

EG_BISHOP_PST = [
    -14, -21, -11,  -8, -7,  -9, -17, -24,
     -8,  -4,   7, -12, -3, -13,  -4, -14,
      2,  -8,   0,  -1, -2,   6,   0,   4,
     -3,   9,  12,   9, 14,  10,   3,   2,
     -6,   3,  13,  19,  7,  10,  -3,  -9,
    -12,  -3,   8,  10, 13,   3,  -7, -15,
    -14, -18,  -7,  -1,  4,  -9, -15, -27,
    -23,  -9, -23,  -5, -9, -16,  -5, -17,
]

MG_ROOK_PST = [
     32,  42,  32,  51, 63,  9,  31,  43,
     27,  32,  58,  62, 80, 67,  26,  44,
     -5,  19,  26,  36, 17, 45,  61,  16,
    -24, -11,   7,  26, 24, 35,  -8, -20,
    -36, -26, -12,  -1,  9, -7,   6, -23,
    -45, -25, -16, -17,  3,  0,  -5, -33,
    -44, -16, -20,  -9, -1, 11,  -6, -71,
    -19, -13,   1,  17, 16,  7, -37, -26,
]

EG_ROOK_PST = [
    13, 10, 18, 15, 12,  12,   8,   5,
    11, 13, 13, 11, -3,   3,   8,   3,
     7,  7,  7,  5,  4,  -3,  -5,  -3,
     4,  3, 13,  1,  2,   1,  -1,   2,
     3,  5,  8,  4, -5,  -6,  -8, -11,
    -4,  0, -5, -1, -7, -12,  -8, -16,
    -6, -6,  0,  2, -9,  -9, -11,  -3,
    -9,  2,  3, -1, -5, -13,   4, -20,
]

MG_QUEEN_PST = [
    -28,   0,  29,  12,  59,  44,  43,  45,
    -24, -39,  -5,   1, -16,  57,  28,  54,
    -13, -17,   7,   8,  29,  56,  47,  57,
    -27, -27, -16, -16,  -1,  17,  -2,   1,
     -9, -26,  -9, -10,  -2,  -4,   3,  -3,
    -14,   2, -11,  -2,  -5,   2,  14,   5,
    -35,  -8,  11,   2,   8,  15,  -3,   1,
     -1, -18,  -9,  10, -15, -25, -31, -50,
]

EG_QUEEN_PST = [
     -9,  22,  22,  27,  27,  19,  10,  20,
    -17,  20,  32,  41,  58,  25,  30,   0,
    -20,   6,   9,  49,  47,  35,  19,   9,
      3,  22,  24,  45,  57,  40,  57,  36,
    -18,  28,  19,  47,  31,  34,  39,  23,
    -16, -27,  15,   6,   9,  17,  10,   5,
    -22, -23, -30, -16, -16, -23, -36, -32,
    -33, -28, -22, -43,  -5, -32, -20, -41,
]

MG_KING_PST = [
    -65,  23,  16, -15, -56, -34,   2,  13,
     29,  -1, -20,  -7,  -8,  -4, -38, -29,
     -9,  24,   2, -16, -20,   6,  22, -22,
    -17, -20, -12, -27, -30, -25, -14, -36,
    -49,  -1, -27, -39, -46, -44, -33, -51,
    -14, -14, -22, -46, -44, -30, -15, -27,
      1,   7,  -8, -64, -43, -16,   9,   8,
    -15,  36,  12, -54,   8, -28,  24,  14,
]

EG_KING_PST = [
    -74, -35, -18, -18, -11,  15,   4, -17,
    -12,  17,  14,  17,  17,  38,  23,  11,
     10,  17,  23,  15,  20,  45,  44,  13,
     -8,  22,  24,  27,  26,  33,  26,   3,
    -18,  -4,  21,  24,  27,  23,   9, -11,
    -19,  -3,  11,  21,  23,  16,   7,  -9,
    -27, -11,   4,  13,  14,   4,  -5, -17,
    -53, -34, -21, -11, -28, -14, -24, -43
]

# CONSTANTS
WHITE_PIECES = ['K', 'Q', 'R', 'B', 'N', 'P']
BLACK_PIECES = ['k', 'q', 'r', 'b', 'n', 'p']

# penalty lookup table, index = total attack score on a king's surrounding area
KING_ATTACK_PENALTIES = [0, 5, 15, 40, 70, 100, 150, 200, 250, 300]

# position is a Board object    
def evaluate_position(position):
    piece_lists = position.piece_lists
    
    # used to calculate interpolated value btwn. end-game (0) & mid-game (1) for PSTs & king safety adjustment
    # phase is determined with pre-defined phase scores for each piece left on the board:
    # Queen = 4, Rook = 2, Bishop = 1, Knight = 1, Maximum Total is 24
    # interpolation formula: (mg-count * (game-phase / max-phase)) + (eg-count * (1 - (game_phase / max-phase)))
    game_phase = 0
    max_phase = 24
    
    # middle game and end game material counts for white and black
    w_mg_eval = 0 
    w_eg_eval = 0 
    b_mg_eval = 0 
    b_eg_eval = 0

    # used to adjust final evaluation based on piece activity
    w_mobility = 0
    b_mobility = 0

    # used to adjust final evaluation based on king safety
    w_king_safety_penalty = 0
    b_king_safety_penalty = 0
    w_king_index = piece_lists['K'][0]
    b_king_index = piece_lists['k'][0]

    # used to adjust final evaluation based on attacks against the area near the enemy king
    w_king_attack_score = 0
    b_king_attack_score = 0

    # used to count attacks on the one-block radius surrounding the enemy kings
    w_king_ring = [w_king_index + delta for delta in KING_DELTAS]
    b_king_ring = [b_king_index + delta for delta in KING_DELTAS]
    
    # update mid-game/end-game material evaluations + PST scores for each piece, increment game_phase
    # King = 20000, Q = 900, R = 500, B = 330, N = 320, P = 100
    for piece in WHITE_PIECES:
        for index in piece_lists[piece]:
            index_64 = TO_64[index]     # convert index to 64-square array for PST lookups
            if piece == 'K':
                w_mg_eval += 20000 + MG_KING_PST[index_64]
                w_eg_eval += 20000 + EG_KING_PST[index_64]
            elif piece == 'Q':
                w_mg_eval += 900 + MG_QUEEN_PST[index_64]
                w_eg_eval += 900 + EG_QUEEN_PST[index_64]

                # update piece mobility score with all accessible empty squares + update attacks on enemy king area
                for direction in QUEEN_DELTAS:
                    for delta in QUEEN_DELTAS[direction]:
                        target_index = index + delta
                        target_square = position.board[target_index]
                        
                        if target_square == OUT_OF_BOUNDS: break

                        if target_square in b_king_ring:
                            w_king_attack_score += 5 # queen attack bonus

                        if target_square == EMPTY:
                            w_mobility += 1
                        else:
                            break # move to next direction if a non-empty / out-of-bounds square is encountered

                game_phase += 4
            elif piece == 'R':
                w_mg_eval += 500 + MG_ROOK_PST[index_64]
                w_eg_eval += 500 + EG_ROOK_PST[index_64]

                # update piece mobility score with all accessible empty squares + update attacks on enemy king area
                for direction in ROOK_DELTAS:
                    for delta in ROOK_DELTAS[direction]:
                        target_index = index + delta
                        target_square = position.board[target_index]
                        
                        if target_square == OUT_OF_BOUNDS: break

                        if target_square in b_king_ring:
                            w_king_attack_score += 4 # rook attack bonus

                        if target_square == EMPTY:
                            w_mobility += 1
                        else:
                            break # move to next direction if a non-empty / out-of-bounds square is encountered

                game_phase += 2
            elif piece == 'B':
                w_mg_eval += 330 + MG_BISHOP_PST[index_64]
                w_eg_eval += 330 + EG_BISHOP_PST[index_64]

                # update piece mobility score with all accessible empty squares + update attacks on enemy king area
                for direction in BISHOP_DELTAS:
                    for delta in BISHOP_DELTAS[direction]:
                        target_index = index + delta
                        target_square = position.board[target_index]
                        
                        if target_square == OUT_OF_BOUNDS: break

                        if target_square in b_king_ring:
                            w_king_attack_score += 2 # bishop attack bonus

                        if target_square == EMPTY:
                            w_mobility += 1
                        else:
                            break # move to next direction if a non-empty / out-of-bounds square is encountered

                game_phase += 1
            elif piece == 'N':
                w_mg_eval += 320 + MG_KNIGHT_PST[index_64]
                w_eg_eval += 320 + EG_KNIGHT_PST[index_64]

                # update piece mobility score with all accessible empty squares + update attacks on enemy king area
                for delta in KNIGHT_DELTAS:
                    target_index = index + delta
                    target_square = position.board[target_index]
                    
                    if target_square == OUT_OF_BOUNDS: continue

                    if target_square in b_king_ring:
                        w_king_attack_score += 2 # knight attack bonus

                    if target_square == EMPTY:
                        w_mobility += 1

                game_phase += 1
            elif piece == 'P':
                w_mg_eval += 100 + MG_PAWN_PST[index_64]
                w_eg_eval += 100 + EG_PAWN_PST[index_64]
                    
    for piece in BLACK_PIECES:
        for index in piece_lists[piece]:
            flipped_index = FLIP[index]     # flip index to adjust PST from white's perspective to black's
            index_64 = TO_64[flipped_index] # convert index to 64-square array for PST lookups
            if piece == 'k':
                b_mg_eval += 20000 + MG_KING_PST[index_64]
                b_eg_eval += 20000 + EG_KING_PST[index_64]
            elif piece == 'q':
                b_mg_eval += 900 + MG_QUEEN_PST[index_64]
                b_eg_eval += 900 + EG_QUEEN_PST[index_64]

                # update piece mobility score with all accessible empty squares + update attacks on enemy king area
                for direction in QUEEN_DELTAS:
                    for delta in QUEEN_DELTAS[direction]:
                        target_index = index + delta
                        target_square = position.board[target_index]
                        
                        if target_square == OUT_OF_BOUNDS: break

                        if target_square in w_king_ring:
                            b_king_attack_score += 5 # queen attack bonus

                        if target_square == EMPTY:
                            b_mobility += 1
                        else:
                            break # move to next direction if a non-empty / out-of-bounds square is encountered

                game_phase += 4
            elif piece == 'r':
                b_mg_eval += 500 + MG_ROOK_PST[index_64]
                b_eg_eval += 500 + EG_ROOK_PST[index_64]

                # update piece mobility score with all accessible empty squares + update attacks on enemy king area
                for direction in ROOK_DELTAS:
                    for delta in ROOK_DELTAS[direction]:
                        target_index = index + delta
                        target_square = position.board[target_index]
                        
                        if target_square == OUT_OF_BOUNDS: break

                        if target_square in w_king_ring:
                            b_king_attack_score += 4 # rook attack bonus

                        if target_square == EMPTY:
                            b_mobility += 1
                        else:
                            break # move to next direction if a non-empty / out-of-bounds square is encountered

                game_phase += 2
            elif piece == 'b':
                b_mg_eval += 330 + MG_BISHOP_PST[index_64]
                b_eg_eval += 330 + EG_BISHOP_PST[index_64]

                # update piece mobility score with all accessible empty squares + update attacks on enemy king area
                for direction in BISHOP_DELTAS:
                    for delta in BISHOP_DELTAS[direction]:
                        target_index = index + delta
                        target_square = position.board[target_index]
                        
                        if target_square == OUT_OF_BOUNDS: break

                        if target_square in w_king_ring:
                            b_king_attack_score += 2 # bishop attack bonus

                        if target_square == EMPTY:
                            b_mobility += 1
                        else:
                            break # move to next direction if a non-empty / out-of-bounds square is encountered

                game_phase += 1
            elif piece == 'n':
                b_mg_eval += 320 + MG_KNIGHT_PST[index_64]
                b_eg_eval += 320 + EG_KNIGHT_PST[index_64]

                # update piece mobility score with all accessible empty squares + update attacks on enemy king area
                for delta in KNIGHT_DELTAS:
                    target_index = index + delta
                    target_square = position.board[target_index]
                    
                    if target_square == OUT_OF_BOUNDS: continue

                    if target_square in w_king_ring:
                        b_king_attack_score += 2 # knight attack bonus

                    if target_square == EMPTY:
                        b_mobility += 1

                game_phase += 1
            elif piece == 'p':
                b_mg_eval += 100 + MG_PAWN_PST[index_64]
                b_eg_eval += 100 + EG_PAWN_PST[index_64]

    # give a penalty to castled kings that are not protected by a "pawn shield"
    for king_color in ['K', 'k']: # uppercase K = white king, lowercase k = black king
        king_file = (w_king_index % 10) if (king_color == 'K') else (b_king_index % 10)
        king_rank = (w_king_index // 10) if (king_color == 'K') else (b_king_index // 10)

        # check pawn shield for white king only if it's on the 1st rank
        if king_color == 'K' and king_rank == 9:
            shield_files = [king_file - 1, king_file, king_file + 1]

            # check the two squares directly in front of each of the king's shield files
            for file in shield_files:
                ideal_shield_square = 80 + file  # index 80 is the start of the second rank
                ideal_square_occupier = position.board[ideal_shield_square]
                pushed_shield_square = 70 + file # index 70 is the start of the third rank
                pushed_square_occupier = position.board[pushed_shield_square]

                # if no friendly pawn found in front of the king, apply a king safety penalty
                if ideal_square_occupier != 'P':
                    if pushed_square_occupier != 'P': 
                        w_king_safety_penalty += 25  # if both 2nd and 3rd ranks have no pawn -> full penalty
                    else:
                        w_king_safety_penalty += 15  # if 2nd rank unprotected but 3rd has a pawn -> reduced penalty
        
        # check pawn shield for black king only if it's on the 8th rank
        if king_color == 'k' and king_rank == 2:
            shield_files = [king_file - 1, king_file, king_file + 1]

            # check the two squares directly in front of each of the king's shield files
            for file in shield_files:
                ideal_shield_square = 30 + file  # index 30 is the start of the seventh rank
                ideal_square_occupier = position.board[ideal_shield_square]
                pushed_shield_square = 40 + file # index 40 is the start of the sixth rank
                pushed_square_occupier = position.board[pushed_shield_square]

                # if no friendly pawn found in front of the king, apply a king safety penalty
                if ideal_square_occupier != 'p':
                    if pushed_square_occupier != 'p':
                        b_king_safety_penalty += 25  # if both 7th and 6th ranks have no pawn -> full penalty
                    else:
                        b_king_safety_penalty += 15  # if 7th rank unprotected but 6th has a pawn -> reduced penalty
    
    # find interpolated evaluations for white and black based on game phase
    game_phase = min(game_phase, max_phase)     # cap game_phase at 24 (in case of early promotions)

    w_interp_eval = (w_mg_eval * (game_phase / max_phase)) + (w_eg_eval * (1 - (game_phase / max_phase)))
    b_interp_eval = (b_mg_eval * (game_phase / max_phase)) + (b_eg_eval * (1 - (game_phase / max_phase)))

    # scale mobility adjustment by a factor of 2
    mobility_adjustment = 2 * (w_mobility - b_mobility)

    # calculate final king safety adjustments
    w_king_safety_penalty += KING_ATTACK_PENALTIES[min(b_king_attack_score, 9)]
    b_king_safety_penalty += KING_ATTACK_PENALTIES[min(w_king_attack_score, 9)]

    # taper penalties with game phase (king safety importance decreases with fewer pieces on the board)
    w_tapered_king_penalty = w_king_safety_penalty * (game_phase / max_phase)
    b_tapered_king_penalty = b_king_safety_penalty * (game_phase / max_phase)
    
    king_safety_adjustment = b_tapered_king_penalty - w_tapered_king_penalty # higher penalty for black = good for white
    
    # final eval: + for white, - for black
    return (w_interp_eval - b_interp_eval) + mobility_adjustment + king_safety_adjustment