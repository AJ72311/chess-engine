from board import Board, Move
from evaluation import evaluate_position
from move_generator import generate_moves

# ----------------------------------- GLOBAL CONSTANTS -----------------------------------
INFINITY = float('inf') # infinity constant

# used in MVV-LVA move-ordering, king value as highest b/c we want king captures to be attempted last
PIECE_VALUES = {'k': 10, 'q': 9, 'r': 5, 'b': 3.3, 'n': 3.2, 'p': 1}   

# used in history table piece identification
# outer-index pieces: 0='P', 1='N', 2='B', 3='R', 4='Q', 5='K', 6='p', 7='n', 8='b', 9='r', 10='q', 11='k'
HISTORY_OUTER_INDICES = {
    'P': 0, 'N': 1, 'B': 2, 'R': 3, 'Q': 4, 'K': 5,
    'p': 6, 'n': 7, 'b': 8, 'r': 9, 'q': 10, 'k': 11,
}

# the Search class contains minimax's wrapper function find_best_move(), this is the algorithm for exploring the game tree
class Search:
    def __init__(self, depth=6):    # initialize depth move-ordering heuristics
        self.depth = depth

        # KILLER TABLE: at each depth, store 'killer' moves: extremely strong quiet moves in sibling node
        # stores a maximum of two killer Move objects for each depth
        self.killer_table = [[None, None] for _ in range(depth + 1)]

        # HISTORY TABLE: stores moves that caused beta cutoffs for use in move-ordering, bonus given for higher depths
        # for each piece type, store a score for all possible destination squares, update when a move creates a beta cutoff
        # all initial scores are 0, bonuses are added based on depth-squared
        self.history_table = [[0] * 120 for _ in range(12)]      

    # MOVE ORDERING: sort the legal_moves to 'guess' which ones will be best, try them first for a fast beta cutoff
    def score_move(self, move, depth):
        if move.piece_captured:             # highest priority: captures, MVV-LVA
            victim_value = PIECE_VALUES[move.piece_captured.lower()]
            attacker_value = PIECE_VALUES[move.moving_piece.lower()]
            return 1000 + victim_value - attacker_value
        elif move in self.killer_table[depth]:   # 2nd priority: quiet 'killer' moves
            return 900
        else:                               # last priority, use history table score 
            # determine moving piece's history-table index 
            pc_type_index = HISTORY_OUTER_INDICES[move.moving_piece]
            return self.history_table[pc_type_index][move.destination_index]    

    # wrapper function for minimax, returns the move with the most favorable evaluation for the provided color_to_play
    def find_best_move(self, root_node, color_to_play, alpha = -INFINITY, beta = INFINITY, depth = 6):    
        # SET UP INITIAL MINIMAX CALL
        legal_moves = generate_moves(root_node)[0] # all legal moves
        best_move = None
        killer_table = self.killer_table
        history_table = self.history_table
            
        # sort legal moves based on move-ordering score in descending order
        # sorting priority: captures w/ MVV-LVA -> killer moves -> history table score
        legal_moves.sort(key=lambda move: self.score_move(move, depth), reverse=True)

        # SET-UP MINIMAX RECURSION
        # white to move
        if color_to_play == 'white':
            best_eval = -INFINITY

            for move in legal_moves:
                root_node.make_move(move)
                move_eval = self.minimax(root_node, alpha, beta, 'black', depth - 1)
                root_node.unmake_move(move)
                if (move_eval > best_eval):
                    best_eval = move_eval
                    best_move = move

                alpha = max(alpha, move_eval)
                if alpha >= beta:       # beta cut-off, update killer and history tables, break
                    if not move.piece_captured:     # if this was not a capture
                        # shift over top two killer moves for this depth
                        killer_table[depth][1] = killer_table[depth][0]
                        killer_table[depth][0] = move

                        # give a bonus of depth^2 to the this piece's history table destination square
                        pc_type_index = HISTORY_OUTER_INDICES[move.moving_piece]
                        dest = move.destination_index
                        history_table[pc_type_index][dest] += depth * depth
                    break
        
        # black to move
        else:
            best_eval = INFINITY

            for move in legal_moves:
                root_node.make_move(move)
                move_eval = self.minimax(root_node, alpha, beta, 'white', depth - 1)
                root_node.unmake_move(move)
                if (move_eval < best_eval):
                    best_eval = move_eval
                    best_move = move

                beta = min(beta, move_eval)
                if (beta <= alpha):     # beta cut-off, update killer and history tables, break
                    if not move.piece_captured:     # if this was not a capture
                        # shift over top two killer moves for this depth
                        killer_table[depth][1] = killer_table[depth][0]
                        killer_table[depth][0] = move

                        # give a bonus of depth^2 to the this piece's history table destination square
                        pc_type_index = HISTORY_OUTER_INDICES[move.moving_piece]
                        dest = move.destination_index
                        history_table[pc_type_index][dest] += depth * depth
                    break

        return best_move

    # recursive game search, minimax + alpha-beta pruning, intial call by find_best_move is below
    def minimax(self, current_position, alpha, beta, color_to_play, depth):
        history_table = self.history_table
        killer_table = self.killer_table

        # generate all legal moves and count the number of checks in the position
        legal_moves, check_count = generate_moves(current_position) # all legal moves

        # BASE CASE: checkmate, stalemate, or depth = 0
        if len(legal_moves) == 0:           # if no legal moves
            if check_count > 0:             # if king is in check, base case #1: it's checkmate
                if current_position.color_to_play == 'white':
                    return -99999 - depth   # white is checkmated, favorable eval for black 
                elif current_position.color_to_play == 'black':
                    return 99999 + depth    # black is checkmated, favorable eval for white
                
            elif check_count == 0:          # if no checks, base case #2: it's stalemate
                return 0                    # stalemate eval
            
        if depth == 0:                      # if depth == 0, base case #3: max depth reached
            return evaluate_position(current_position)
        
        # RECURSIVE CASE: 
        # sort legal moves based on move-ordering score in descending order
        # sorting priority: captures w/ MVV-LVA -> killer moves -> history table score
        legal_moves.sort(key=lambda move: self.score_move(move, depth), reverse=True)

        if color_to_play == 'white': # white to move
            max_eval = -INFINITY

            for move in legal_moves:
                current_position.make_move(move)
                returned_eval = self.minimax(current_position, alpha, beta, 'black', depth - 1)  # recursive call
                current_position.unmake_move(move)

                max_eval = max(max_eval, returned_eval)
                alpha = max(alpha, returned_eval)

                if alpha >= beta:   # beta cut-off, update killer and history tables, break
                    if not move.piece_captured:     # if this was not a capture
                        # shift over top two killer moves for this depth
                        killer_table[depth][1] = killer_table[depth][0]
                        killer_table[depth][0] = move

                        # give a bonus of depth^2 to the this piece's history table destination square
                        pc_type_index = HISTORY_OUTER_INDICES[move.moving_piece]
                        dest = move.destination_index
                        history_table[pc_type_index][dest] += depth * depth
                    break

            return max_eval

        else: # black to move
            min_eval = INFINITY

            for move in legal_moves:
                current_position.make_move(move)
                returned_eval = self.minimax(current_position, alpha, beta, 'white', depth - 1)  # recursive call
                current_position.unmake_move(move)

                min_eval = min(min_eval, returned_eval)
                beta = min(beta, returned_eval)

                if beta <= alpha:   # beta cut-off, update killer and history tables, break
                    if not move.piece_captured:     # if this was not a capture
                        # shift over top two killer moves for this depth
                        killer_table[depth][1] = killer_table[depth][0]
                        killer_table[depth][0] = move

                        # give a bonus of depth^2 to the this piece's history table destination square
                        pc_type_index = HISTORY_OUTER_INDICES[move.moving_piece]
                        dest = move.destination_index
                        history_table[pc_type_index][dest] += depth * depth
                    break
            
            return min_eval