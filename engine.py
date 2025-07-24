from board import Board, Move
from evaluation import evaluate_position
from move_generator import generate_moves

# ----------------------------------- RECURSIVE GAME TREE EXPLORATION, FINDING BEST MOVE -----------------------------------
INFINITY = float('inf') # infinity constant

# used in MVV-LVA move-ordering, king value as highest b/c we want king captures to be attempted last
PIECE_VALUES = {'k': 10, 'q': 9, 'r': 5, 'b': 3.3, 'n': 3.2, 'p': 1}     

# MOVE ORDERING: sort the legal_moves to 'guess' which ones will be best, try them first for a fast beta cutoff
# captures should be searched first, so they get a high base sorting score of 1000
# MVV-LVA: use weakest friendly piece to capture most valuable enemy piece: score = victim_value - attacker_value
def score_move(move):
    if move.piece_captured:
        victim_value = PIECE_VALUES[move.piece_captured.lower()]
        attacker_value = PIECE_VALUES[move.moving_piece.lower()]
        return 1000 + victim_value - attacker_value
    else:
        return 100  # temporary base score for non-captures, will be changed later

# helper function for minimax, returns the move with the most favorable evaluation for the provided color_to_play
def find_best_move(root_node, color_to_play, alpha = -INFINITY, beta = INFINITY, depth = 6):
    legal_moves = generate_moves(root_node)[0] # all legal moves
    best_move = None
        
    # sort legal moves based on move-ordering score in descending order
    legal_moves.sort(key=score_move, reverse=True)

    # white to move
    if color_to_play == 'white':
        best_eval = -INFINITY

        for move in legal_moves:
            root_node.make_move(move)
            move_eval = minimax(root_node, alpha, beta, 'black', depth - 1)
            root_node.unmake_move(move)
            if (move_eval > best_eval):
                best_eval = move_eval
                best_move = move

            alpha = max(alpha, move_eval)
            if alpha >= beta:
                break
    
    # black to move
    else:
        best_eval = INFINITY

        for move in legal_moves:
            root_node.make_move(move)
            move_eval = minimax(root_node, alpha, beta, 'white', depth - 1)
            root_node.unmake_move(move)
            if (move_eval < best_eval):
                best_eval = move_eval
                best_move = move

            beta = min(beta, move_eval)
            if (beta <= alpha):
                break

    return best_move
    
def minimax(current_position, alpha, beta, color_to_play, depth):
    # generate all legal moves and count the number of checks in the position
    legal_moves, check_count = generate_moves(current_position) # all legal moves
        
    # sort legal moves based on move-ordering score in descending order
    legal_moves.sort(key=score_move, reverse=True)

    # BASE CASE: checkmate, stalemate, or depth = 0
    if len(legal_moves) == 0:           # if no legal moves
        if check_count > 0:             # if king is in check, base case #1: it's checkmate
            if current_position.color_to_play == 'white':
                return -99999 + depth   # white is checkmated, favorable eval for black 
            elif current_position.color_to_play == 'black':
                return 99999 - depth    # black is checkmated, favorable eval for white
            
        elif check_count == 0:          # if no checks, base case #2: it's stalemate
            return 0                    # stalemate eval
        
    if depth == 0:                      # if depth == 0, base case #3: max depth reached
        return evaluate_position(current_position)
    
    # RECURSIVE CASE: 
    if color_to_play == 'white': # white to move
        max_eval = -INFINITY

        for move in legal_moves:
            current_position.make_move(move)
            returned_eval = minimax(current_position, alpha, beta, 'black', depth - 1)  # recursive call
            current_position.unmake_move(move)

            max_eval = max(max_eval, returned_eval)
            alpha = max(alpha, returned_eval)

            if alpha >= beta:   # alpha-beta pruning condition
                break

        return max_eval

    else: # black to move
        min_eval = INFINITY

        for move in legal_moves:
            current_position.make_move(move)
            returned_eval = minimax(current_position, alpha, beta, 'white', depth - 1)  # recursive call
            current_position.unmake_move(move)

            min_eval = min(min_eval, returned_eval)
            beta = min(beta, returned_eval)

            if beta <= alpha:   # alpha-beta pruning condition
                break
        
        return min_eval