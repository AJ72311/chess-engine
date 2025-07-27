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
    def __init__(self, depth=5):    # initialize depth, move-ordering heuristics
        self.depth = depth

        # KILLER TABLE: at each depth, store 'killer' moves: extremely strong quiet moves in sibling node
        # stores a maximum of two killer Move objects for each depth
        self.killer_table = [[None, None] for _ in range(depth + 1)]

        # HISTORY TABLE: stores moves that caused beta cutoffs for use in move-ordering, bonus given for higher depths
        # for each piece type, store a score for all possible destination squares, update when a move creates a beta cutoff
        # all initial scores are 0, bonuses are added based on depth-squared
        self.history_table = [[0] * 120 for _ in range(12)]  

        # TRANSPOSITION TABLE: a hash table of previously encountered positions
        # if position was fully evaluated, skip the branch, otherwise update alpha/beta if it tightens the search window
        self.transposition_table = {} 

    # MOVE ORDERING: sort the legal_moves to 'guess' which ones will be best, try them first for a fast beta cutoff
    def score_move(self, move, depth, hash_move=None):
        if hash_move is not None and move == hash_move:     # top priority: hash moves from transposition table
            return 2000
        
        elif move.piece_captured:                           # 2nd priority: captures, MVV-LVA
            victim_value = PIECE_VALUES[move.piece_captured.lower()]
            attacker_value = PIECE_VALUES[move.moving_piece.lower()]
            return 1000 + (victim_value * 10) - attacker_value
        
        elif move in self.killer_table[depth]:              # 3rd priority: quiet 'killer' moves
            return 900
        
        else:                                               # last priority, use history table score 
            # determine moving piece's history-table index 
            pc_type_index = HISTORY_OUTER_INDICES[move.moving_piece]
            return self.history_table[pc_type_index][move.destination_index]    

    # wrapper function for minimax, returns the move with the most favorable evaluation for the provided color_to_play
    def find_best_move(self, root_node, color_to_play, alpha = -INFINITY, beta = INFINITY, depth = 5):    
        # SET UP INITIAL MINIMAX CALL
        legal_moves = generate_moves(root_node)[0] # all legal moves
        best_move = None
        killer_table = self.killer_table
        history_table = self.history_table
            
        # sort legal moves based on move-ordering score in descending order
        # sorting priority: captures w/ MVV-LVA -> killer moves -> history table score
        # note: hash moves are not used at the root
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
        transposition_table = self.transposition_table

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
            return self.quiescence_search(current_position, alpha, beta, color_to_play) # enter quiescence routine
        
        # RECURSIVE CASE: 
        original_alpha = alpha
        original_beta = beta

        # before searching, check transposition table for previous encounters of this position
        hash_move = None    # the strongest move to be retrieved from the transposition table for precise move-ordering 
        position_hash = current_position.zobrist_hash
        if position_hash in transposition_table:
            entry = transposition_table[position_hash]
            stored_eval = entry['eval']
            stored_depth = entry['depth']
            stored_flag = entry['flag']
            if 'best_move' in entry:
                hash_move = entry['best_move']

            if stored_depth >= depth:               # only trust evals from depths >= current depth
                if stored_flag == 'EXACT':          # node was evaluated to the leaves, evaluation is exact
                    return stored_eval
                elif stored_flag == 'LOWERBOUND':   # beta cut-off occured
                    if stored_eval > alpha:         # if stored eval is greater than alpha, update alpha to it
                        alpha = stored_eval
                elif stored_flag == 'UPPERBOUND':   # alpha was never improved
                    if stored_eval < beta:          # if stored eval is lower than beta, update beta to it
                        beta = stored_eval
                    
                if alpha >= beta:                   # if updated alpha/beta vals now meet the pruning condition
                    return stored_eval

        # if transposition table didn't contain position, or didn't sufficiently tighten alpha/beta window, proceed
        # sort legal moves based on move-ordering score in descending order
        # sorting priority: hash move -> captures w/ MVV-LVA -> killer moves -> history table score
        legal_moves.sort(key=lambda move: self.score_move(move, depth, hash_move), reverse=True)

        if color_to_play == 'white': # white to move
            max_eval = -INFINITY
            best_move = None         # track best move to store in TT for move-ordering

            for move in legal_moves:
                current_position.make_move(move)
                returned_eval = self.minimax(current_position, alpha, beta, 'black', depth - 1)  # recursive call
                current_position.unmake_move(move)

                if returned_eval > max_eval:
                    max_eval = returned_eval
                    best_move = move

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

            # after search completion, update transposition table
            if max_eval <= original_alpha:      # alpha was never raised
                flag = 'UPPERBOUND'
            elif max_eval >= beta:              # a beta cutoff occurred
                flag = 'LOWERBOUND'
            else:                               # search was completed with improvements in alpha and no beta cutoffs
                flag = 'EXACT'
            
            # create new entry / update existing entry in transposition table
            transposition_table[position_hash] = {
                'eval': max_eval,
                'depth': depth,
                'flag': flag,
                'best_move': best_move
            }

            return max_eval

        else: # black to move
            min_eval = INFINITY
            best_move = None     # track the best move to store in TT for move-ordering

            for move in legal_moves:
                current_position.make_move(move)
                returned_eval = self.minimax(current_position, alpha, beta, 'white', depth - 1)  # recursive call
                current_position.unmake_move(move)

                if returned_eval < min_eval:
                    min_eval = returned_eval
                    best_move = move

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
            
            # after search completion, update transposition table
            if min_eval <= alpha:               # alpha cut-off occurred, true score is at most min_eval
                flag = 'UPPERBOUND'
            elif min_eval >= original_beta:     # search failed low, couldn't improve on original beta
                flag = 'LOWERBOUND'
            else:                               # search was completed within alpha-beta window, score is exact
                flag = 'EXACT'

            # create new entry / update existing entry in transposition table
            transposition_table[position_hash] = {
                'eval': min_eval,
                'depth': depth,
                'flag': flag,
                'best_move': best_move
            }
            
            return min_eval

    # extends search at minimax leaf nodes to mitigate the 'horizon effect', only considers captures / check escapes
    # hard coded depth limit of 8 to lockdown any runaway recursions
    def quiescence_search(self, current_position, alpha, beta, color_to_play, depth=8):
        # STEP 1: BASE CASES & MOVE GENERATION
        legal_moves, check_count = generate_moves(current_position)

        # first base case: stalemates / checkmates, return eval if found
        if len(legal_moves) == 0:           # if no legal moves
            if check_count > 0:             # if king is in check, it's checkmate
                if current_position.color_to_play == 'white':
                    return -99999 - depth   # white is checkmated, favorable eval for black 
                elif current_position.color_to_play == 'black':
                    return 99999 + depth    # black is checkmated, favorable eval for white
                
            elif check_count == 0:          # if no checks, it's stalemate
                return 0                    # stalemate eval
        
        # only filter out non-captures if no checks... if a king is in check, we must evaluate all legal moves
        if check_count == 0:
            legal_moves = [move for move in legal_moves if move.piece_captured]

        # second base case: hardcoded depth limit reached
        if depth == 0: 
            return evaluate_position(current_position)

        # STEP 2: "STAND-PAT" PRUNING
        stand_pat_eval = evaluate_position(current_position)
        if color_to_play == 'white':            # white to move
            if stand_pat_eval >= beta:          # fail high, black has a better option
                return beta
            alpha = max(alpha, stand_pat_eval)  # update alpha if the stand pat eval improves on it
        elif color_to_play == 'black':          # black to move
            if stand_pat_eval <= alpha:         # fail low, white has a better option
                return alpha 
            beta = min(beta, stand_pat_eval)    # update beta if the stand pat eval improves on it
            
        # third base case: no captures / check evasion moves available
        if len(legal_moves) == 0:
            return stand_pat_eval

        # STEP 3: RECURSIVE CASE - SAME AS MINIMAX SEARCH, BUT SCOPE LIMITED TO CAPTURES / CHECK-EVASION ONLY
        # move-ordering - sort captures using MVV-LVA
        legal_moves.sort(key=lambda move: self.score_move(move, 0), reverse=True)

        if color_to_play == 'white':
            for move in legal_moves:
                current_position.make_move(move)
                returned_eval = self.quiescence_search(current_position, alpha, beta, 'black', depth-1)
                current_position.unmake_move(move)

                alpha = max(alpha, returned_eval)

                if alpha >= beta:
                    return beta
                
            return alpha

        elif color_to_play == 'black':
            for move in legal_moves:
                current_position.make_move(move)
                returned_eval = self.quiescence_search(current_position, alpha, beta, 'white', depth-1)
                current_position.unmake_move(move)

                beta = min(beta, returned_eval)

                if beta <= alpha:
                    return alpha
                
            return beta
    