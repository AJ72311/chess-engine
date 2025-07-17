from board import Board, Move
from evaluation import evaluate_position
from move_generator import generate_moves

# ----------------------------------- RECURSIVE GAME TREE EXPLORATION, FINDING BEST MOVE -----------------------------------
INFINITY = float('inf') # infinity constant

# helper function for minimax, returns the move with the most favorable evaluation for the provided color_to_play
def find_best_move(root_node, color_to_play, alpha = -INFINITY, beta = INFINITY, depth = 5):
    legal_moves = generate_moves(root_node) # Look into move-ordering for this
    best_move = None

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
    # BASE CASE: checkmate, stalemate, depth = 0
    if current_position.is_game_over() or depth == 0:
        return evaluate_position(current_position)
    
    # RECURSIVE CASE: 
    if color_to_play == 'white': # white to move
        max_eval = -INFINITY

        legal_moves = generate_moves(current_position) # Look into move-ordering for this
        for move in legal_moves:
            current_position.make_move(move)
            returned_eval = minimax(current_position, alpha, beta, 'black', depth - 1)
            current_position.unmake_move(move)

            max_eval = max(max_eval, returned_eval)
            alpha = max(alpha, returned_eval)

            if alpha >= beta:
                break

        return max_eval

    else: # black to move
        min_eval = INFINITY

        legal_moves = generate_moves(current_position) # Look into move-ordering for this
        for move in legal_moves:
            current_position.make_move(move)
            returned_eval = minimax(current_position, alpha, beta, 'white', depth - 1)
            current_position.unmake_move(move)

            min_eval = min(min_eval, returned_eval)
            beta = min(beta, returned_eval)

            if beta <= alpha:
                break
        
        return min_eval