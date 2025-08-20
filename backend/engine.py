# for search
from board import Board, Move
from evaluation import evaluate_position
from move_generator import generate_moves
import time

# for opening book
import chess
import chess.polyglot
from utils import board_to_fen, ALGEBRAIC_TO_INDEX
from utils import parse_user_move

# ----------------------------------- GLOBAL CONSTANTS -----------------------------------
INFINITY = float('inf') # infinity constant
MAX_DEPTH = 64 # used to initialize killer table

# used in MVV-LVA move-ordering, king value as highest b/c we want king captures to be attempted last
PIECE_VALUES = {'k': 10, 'q': 9, 'r': 5, 'b': 3.3, 'n': 3.2, 'p': 1}   

# used in history table piece identification
# outer-index pieces: 0='P', 1='N', 2='B', 3='R', 4='Q', 5='K', 6='p', 7='n', 8='b', 9='r', 10='q', 11='k'
HISTORY_OUTER_INDICES = {
    'P': 0, 'N': 1, 'B': 2, 'R': 3, 'Q': 4, 'K': 5,
    'p': 6, 'n': 7, 'b': 8, 'r': 9, 'q': 10, 'k': 11,
}

# used in delta pruning for quiescence search
DELTA = 100

# margins for futility pruning, indexed by remaining depth
FUTILITY_MARGINS = [0, 100, 300]

# the Search class contains minimax's wrapper function search_root(), this is the algorithm for exploring the game tree
class Search:
    class TimeUpError(Exception):
        # Exception raised when the time limit for a search is exceeded
        pass

    def __init__(self, depth=64):    # initialize max possible depth, move-ordering heuristics
        self.depth = depth
        self.max_q_depth = 0         # track maximum depth reached in quiescence search
        self.nodes_searched = 0      # track total positions explored per root search

        # KILLER TABLE: at each depth, store 'killer' moves: extremely strong quiet moves in sibling node
        # stores a maximum of two killer Move objects for each depth
        self.killer_table = [[None, None] for _ in range(MAX_DEPTH + 1)]

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

    # iterative deepening wrapper for search_root
    def find_best_move(self, root_node, color_to_play, time_limit=5):
        book_move_uci = None

        # check opening book before searching, only within first 20 ply
        if root_node.ply < 20:
            book_move_uci = get_book_move(root_node)

        if book_move_uci: # if opening book contains a move for this position
            legal_moves, _ = generate_moves(root_node) # get legal moves to find the book move's corresponding move object
            move_to_play = parse_user_move(book_move_uci, legal_moves) # get move object and convert to algebraic uci format

            if move_to_play:
                return {
                    'move': move_to_play,
                    'depth': None,
                    'nodes': None,
                    'is_book': True,
                }
            else:
                # safety check in case book is corrupted
                print('Warning: book move was illegal, proceeding with search')
        
        # if no book move found, proceed with normal search
        start_time = time.time()
        self.nodes_searched = 0
        last_completed_depth = 0
        final_best_move = None

        # use a try/catch block to catch TimeUp errors
        try:
            # iterative deepening loop, increments search depth until reaching max depth or time limit
            for depth in range(1, self.depth + 1):
                # make a copy of the board to search on, this prevents time cutoffs from corrupting the original board
                search_board = root_node.copy()
                
                self.max_q_depth = 0    # reset max quiescence depth at each iteration

                # check time limit before initiating a new root search
                if (time.time() - start_time) > time_limit:
                    print(f'Time limit reached before depth {depth}, using last best move')
                    break

                # search the best move at the loop's current depth
                best_move_this_depth = self.search_root(
                    search_board, 
                    color_to_play, 
                    -INFINITY, 
                    INFINITY, 
                    depth,
                    time_limit,
                    start_time,
                    final_best_move # the best move from the last depth, used in root-level move-ordering
                )

                if best_move_this_depth is not None:
                    final_best_move = best_move_this_depth  # update overall best move to current depth's best move
                    last_completed_depth = depth
                    time_elapsed = time.time() - start_time
                    print(f'Depth {depth} completed in {time_elapsed:.2f}s')
                else:
                    # if search was inconclusive, stop and use previous depth's best move
                    print(f"Search at depth {depth} was inconclusive. Using best move from depth {depth - 1}")
                    break
            
        except self.TimeUpError:
            print('Time limit reached. Using best move from the last completed depth')

        return {
            'move': final_best_move,
            'depth': last_completed_depth,
            'nodes': self.nodes_searched,
            'is_book': False,
        }

    # wrapper function for minimax, returns the move with the most favorable evaluation for the provided color_to_play
    def search_root(
            self, root_node, color_to_play, alpha = -INFINITY, beta = INFINITY, 
            depth = 5, time_limit = None, start_time = None, best_move_last_depth = None
        ):    
        # SET UP INITIAL MINIMAX CALL
        legal_moves, _ = generate_moves(root_node) # all legal moves
        best_move = None
        killer_table = self.killer_table
        history_table = self.history_table
            
        # sort legal moves based on move-ordering score in descending order
        # sorting priority: captures w/ MVV-LVA -> killer moves -> history table score
        # note: hash moves are not used at the root
        legal_moves.sort(key=lambda move: self.score_move(move, depth), reverse=True)

        # best move from last iterative-deepening depth always gets top priority
        if best_move_last_depth in legal_moves:
            legal_moves.remove(best_move_last_depth)
            legal_moves.insert(0, best_move_last_depth) # re-insert at the start of the move list

        # SET-UP MINIMAX RECURSION
        # white to move
        if color_to_play == 'white':
            best_eval = -INFINITY

            for move in legal_moves:
                root_node.make_move(move)
                move_eval = self.minimax(root_node, alpha, beta, 'black', depth - 1, time_limit, start_time)
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
                move_eval = self.minimax(root_node, alpha, beta, 'white', depth - 1, time_limit, start_time)
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

    # recursive game search, minimax + alpha-beta pruning, initiated by search_root()
    def minimax(self, current_position, alpha, beta, color_to_play, depth, time_limit, start_time):
        # check if time limit exceeded before searching
        if (time.time() - start_time) > time_limit:
            raise self.TimeUpError()

        self.nodes_searched += 1

        # BASE CASE 1: threefold repetitions
        if current_position.is_repetition():
            return 0 # draw score

        history_table = self.history_table
        killer_table = self.killer_table
        transposition_table = self.transposition_table

        # generate all legal moves and count the number of checks in the position
        legal_moves, check_count = generate_moves(current_position) # all legal moves

        # BASE CASE 2: checkmate, stalemate, fifty move rule, or depth = 0
        if len(legal_moves) == 0:           # if no legal moves
            if check_count > 0:             # if king is in check, base case #1: it's checkmate
                if current_position.color_to_play == 'white':
                    return -99999 - depth   # white is checkmated, favorable eval for black 
                elif current_position.color_to_play == 'black':
                    return 99999 + depth    # black is checkmated, favorable eval for white
                
            elif check_count == 0:          # if no checks, base case #2: it's stalemate
                return 0                    # stalemate eval
        
        # check for fifty move rule draws
        if current_position.fifty_move_criteria_met():
            return 0 # draw score
            
        if depth == 0:                      # if depth == 0, base case #3: max depth reached
            # enter quiescence routine
            return self.quiescence_search(current_position, alpha, beta, color_to_play, time_limit, start_time)
        
        # RECURSIVE CASE: 

        # futility pruning setup
        futility_enabled = False
        static_eval = 0
        if depth <= 2 and check_count == 0: # only allow futility pruning if no checks and depth is below 3
            futility_enabled = True
            static_eval = evaluate_position(current_position)

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

            for move_index, move in enumerate(legal_moves):
                # first, check if futility pruning applies
                if futility_enabled:
                    if not move.piece_captured and not move.promotion_piece: # futility pruning only for quiet moves
                        margin = FUTILITY_MARGINS[depth]

                        # if current eval + safety margin still can't raise alpha
                        if (static_eval + margin) <= alpha:
                            continue # skip to next move

                current_position.make_move(move)

                # 1: full window (alpha, beta) search for the first move
                if move_index == 0:
                    returned_eval = self.minimax(
                        current_position, 
                        alpha, 
                        beta, 
                        'black', 
                        depth - 1, 
                        time_limit, 
                        start_time
                    )
                
                # 2: null window (alpha, alpha+1) search for all subsequent moves
                else:
                    reduction = 0   # used in late-move reductions
                    
                    # LMR conditions
                    if (
                        (depth >= 3)
                        and (move_index >= 3) 
                        and (not move.piece_captured) 
                        and (not move.promotion_piece)
                        and (check_count == 0)
                    ):
                        reduction = 1   # reduce depth for late moves

                    # apply reduction (if any) to the search
                    reduced_depth = depth - 1 - reduction

                    returned_eval = self.minimax(
                        current_position, 
                        alpha, 
                        alpha + 1, 
                        'black', 
                        reduced_depth, 
                        time_limit, 
                        start_time
                    )

                    # 3: if null window search failed high, re-search with a full window to full depth
                    if returned_eval > alpha and returned_eval < beta:
                        returned_eval = self.minimax(
                            current_position, 
                            alpha, 
                            beta, 
                            'black', 
                            depth - 1, 
                            time_limit, 
                            start_time
                        )

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
            if max_eval <= original_alpha:      
                flag = 'UPPERBOUND'
                max_eval = original_alpha
            elif max_eval >= original_beta:              
                flag = 'LOWERBOUND'
                max_eval = original_beta
            else:                               
                flag = 'EXACT'
            
            # create new entry / update existing entry in transposition table
            old = transposition_table.get(position_hash)
            if (not old) or (depth >= old['depth']): # only write to TT if at deeper iteration than existing entry
                entry = {
                    'eval': max_eval,
                    'depth': depth,
                    'flag': flag,
                }
                if flag == 'EXACT': # only store a hash move for move-ordering if evaluation was exact
                    entry['best_move'] = best_move

                transposition_table[position_hash] = entry

            return max_eval

        else: # black to move
            min_eval = INFINITY
            best_move = None     # track the best move to store in TT for move-ordering

            for move_index, move in enumerate(legal_moves):
                # first, check if futility pruning applies
                if futility_enabled:
                    if not move.piece_captured and not move.promotion_piece: # futility pruning only for quiet moves
                        margin = FUTILITY_MARGINS[depth]

                        # if current eval - safety margin still can't lower beta
                        if (static_eval - margin) >= beta:
                            continue # skip to next move

                current_position.make_move(move)

                # 1: full window (alpha, beta) search for the first move
                if move_index == 0:
                    returned_eval = self.minimax(
                        current_position, 
                        alpha, 
                        beta, 
                        'white', 
                        depth - 1, 
                        time_limit, 
                        start_time
                    )

                # 2: null window (beta - 1, beta) search for all subsequent moves
                else:
                    reduction = 0   # used in late-move reductions
                    
                    # LMR conditions
                    # LMR conditions
                    if (
                        (depth >= 3)
                        and (move_index >= 3) 
                        and (not move.piece_captured) 
                        and (not move.promotion_piece)
                        and (check_count == 0)
                    ):
                        reduction = 1   # reduce depth for late moves

                    # apply reduction (if any) to the search
                    reduced_depth = depth - 1 - reduction

                    returned_eval = self.minimax(
                        current_position, 
                        beta - 1, 
                        beta, 
                        'white', 
                        reduced_depth, 
                        time_limit, 
                        start_time
                    )

                    # 3: if null window search failed low, re-search with a full window to full depth
                    if returned_eval < beta and returned_eval > alpha:
                        returned_eval = self.minimax(
                            current_position, 
                            alpha, 
                            beta, 
                            'white', 
                            depth - 1, 
                            time_limit, 
                            start_time
                        )

                current_position.unmake_move(move)

                if returned_eval < min_eval:
                    min_eval = returned_eval
                    best_move = move

                beta = min(beta, returned_eval)

                if beta <= alpha:   # alpha cut-off, update killer and history tables, break
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
            if min_eval <= original_alpha:      
                flag = 'UPPERBOUND'
                min_eval = original_alpha
            elif min_eval >= original_beta:              
                flag = 'LOWERBOUND'
                min_eval = original_beta
            else:                               
                flag = 'EXACT'

            # create new entry / update existing entry in transposition table
            old = transposition_table.get(position_hash)
            if (not old) or (depth >= old['depth']): # only write to TT if at deeper iteration than existing entry
                entry = {
                    'eval': min_eval,
                    'depth': depth,
                    'flag': flag,
                }
                if flag == 'EXACT': # only store a hash move for move-ordering if evaluation was exact
                    entry['best_move'] = best_move

                transposition_table[position_hash] = entry
            
            return min_eval

    # extends search at minimax leaf nodes to mitigate the 'horizon effect', only considers captures / check escapes
    # hard coded depth limit of 8 to lockdown any runaway recursions
    def quiescence_search(
        self, current_position, alpha, beta, color_to_play, 
        time_limit, start_time, q_depth=1, max_depth=8
    ):
        
        self.max_q_depth = max(self.max_q_depth, q_depth)

        # before searching, check if time limit exceeded
        if (time.time() - start_time) > time_limit:
            raise self.TimeUpError()
        
        self.nodes_searched += 1

        # STEP 1: BASE CASES & MOVE GENERATION
        legal_moves, check_count = generate_moves(current_position)

        # first base case: stalemates / checkmates, return eval if found
        if len(legal_moves) == 0:           # if no legal moves
            if check_count > 0:             # if king is in check, it's checkmate
                if current_position.color_to_play == 'white':
                    return -99999 + q_depth   # white is checkmated, favorable eval for black 
                elif current_position.color_to_play == 'black':
                    return 99999 - q_depth    # black is checkmated, favorable eval for white
                
            elif check_count == 0:          # if no checks, it's stalemate
                return 0                    # stalemate eval
        
        # only filter out non-captures if no checks... if a king is in check, we must evaluate all legal moves
        if check_count == 0:
            legal_moves = [move for move in legal_moves if move.piece_captured]
            if not legal_moves: # if there are no legal non-captures, return the final evaluation
                return evaluate_position(current_position)

        # second base case: hardcoded depth limit reached
        if q_depth >= max_depth: 
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

        # STEP 3: RECURSIVE CASE - SAME AS MINIMAX SEARCH, BUT SCOPE LIMITED TO CAPTURES / CHECK-EVASIONS ONLY
        # move-ordering - sort captures using MVV-LVA
        legal_moves.sort(key=lambda move: self.score_move(move, 0), reverse=True)

        if color_to_play == 'white':
            max_eval = stand_pat_eval
            for move in legal_moves:
                # first run delta pruning check
                if check_count == 0: # cannot delta prune while in check
                    attacker_value = PIECE_VALUES[move.moving_piece.lower()]
                    victim_value = PIECE_VALUES[move.piece_captured.lower()]
                    material_gain = (victim_value - attacker_value) * 100 # multiply by 100 for centipawn eval

                    if stand_pat_eval + DELTA + material_gain < alpha:
                        continue # prune

                # if no delta prune, proceed
                current_position.make_move(move)
                returned_eval = self.quiescence_search(
                    current_position, alpha, beta, 'black', 
                    time_limit, start_time, q_depth+1, max_depth
                )
                current_position.unmake_move(move)

                max_eval = max(max_eval, returned_eval)
                alpha = max(alpha, returned_eval)

                if alpha >= beta:
                    return beta
                
            return max_eval

        elif color_to_play == 'black':
            min_eval = stand_pat_eval
            for move in legal_moves:
                # first run delta pruning check
                if check_count == 0: # cannot delta prune while in check
                    attacker_value = PIECE_VALUES[move.moving_piece.lower()]
                    victim_value = PIECE_VALUES[move.piece_captured.lower()]
                    material_gain = (victim_value - attacker_value) * 100 # multiply by 100 for centipawn eval

                    if stand_pat_eval - DELTA - material_gain > beta:
                        continue # prune

                # if no delta prune, proceed
                current_position.make_move(move)
                returned_eval = self.quiescence_search(
                    current_position, alpha, beta, 'white', 
                    time_limit, start_time, q_depth+1, max_depth
                )
                current_position.unmake_move(move)

                min_eval = min(min_eval, returned_eval)
                beta = min(beta, returned_eval)

                if beta <= alpha:
                    return alpha
                
            return min_eval

# helper function, retreives a move from the opening book if available
# returns the book move in UCI format if found, otherwise None
def get_book_move(position, book_path='book.bin'):
    try:
        with chess.polyglot.open_reader(book_path) as reader:
            fen = board_to_fen(position) # convert the board representation to fen format
            board = chess.Board(fen)     # create a python-chess board using the fen

            # find the best weighted move for the position
            entry = reader.find(board)
            book_move = entry.move

            # return the book move in uci format (e.g. e2e4)
            print(f'Book move found: {book_move.uci()}')
            return book_move.uci()

    except (FileNotFoundError):
        print(f'Error: opening book file not found at {book_path}')
    except (IndexError):
        return None # an IndexError means the position was not found in the book
