import random
import copy

# GLOBAL VARIABLES
from utils import TO_64

PIECE_CODES = {         # used to map each piece to an array index in zorbist table for pieces
    'P': 0, 'N': 1, 'B': 2, 'R': 3, 'Q': 4, 'K': 5, 
    'p': 6, 'n': 7, 'b': 8, 'r': 9, 'q': 10, 'k': 11
}

# global random Zobrist values, 64-bit ints, used to compute init. position's hash & incremented with XORs when making moves
random.seed(0)      # for reproducibility

# unique int for each piece-square combination: 12 pieces (6 white + 6 black), 64 board squares
ZOBRIST_PIECE_KEYS = [[random.getrandbits(64) for _ in range(12)] for _ in range(64)]
# castling rights: 16 possibilities
ZOBRIST_CASTLING_KEYS = [random.getrandbits(64) for _ in range(16)]
# en passant file keys: 8 files
ZOBRIST_EP_KEYS = [random.getrandbits(64) for _ in range(8)]
# side to move key
ZOBRIST_COLOR_KEY = random.getrandbits(64)

# BOARD AND MOVE CLASSES
class Board:
    def __init__(self):
        # board_representation, uppercase letters for white, lowercase for black
        # "R" = Rook, "N" = Knight, "B" = Bishop, "Q" = Queen, "K" = King, "P" = Pawn, "#" = Empty, -1 = Out of Bounds
        self.board = [
            -1,  -1,  -1,  -1,  -1,  -1,  -1,  -1,  -1, -1,
            -1,  -1,  -1,  -1,  -1,  -1,  -1,  -1,  -1, -1,
            -1, 'r', 'n', 'b', 'q', 'k', 'b', 'n', 'r', -1,
            -1, 'p', 'p', 'p', 'p', 'p', 'p', 'p', 'p', -1,
            -1, '#', '#', '#', '#', '#', '#', '#', '#', -1,
            -1, '#', '#', '#', '#', '#', '#', '#', '#', -1,
            -1, '#', '#', '#', '#', '#', '#', '#', '#', -1,
            -1, '#', '#', '#', '#', '#', '#', '#', '#', -1,
            -1, 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'P', -1,
            -1, 'R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R', -1,
            -1,  -1,  -1,  -1,  -1,  -1,  -1,  -1,  -1, -1,
            -1,  -1,  -1,  -1,  -1,  -1,  -1,  -1,  -1, -1
        ]
        self.color_to_play = 'white'
        
        # castling rights
        self.white_castle_kingside = True
        self.white_castle_queenside = True
        self.black_castle_kingside = True
        self.black_castle_queenside = True
        
        self.half_move = 0                  # tracks captures and pawn advances for fifty move rule 
        self.ply = 0                        # tracks half-moves since game start
        
        self.en_passant_square = None       # target square for en passant if applicable, reset at each ply
            
        self.piece_lists = {                # directly track each piece's index on the board
            'K': [], 'Q': [], 'R': [], 'B': [], 'N': [], 'P': [],
            'k': [], 'q': [], 'r': [], 'b': [], 'n': [], 'p': []
        }
        
        self.initialize_piece_lists()            # initialize piece list indices
        self.zobrist_hash = self.compute_hash()  # a hash of the position, used in engine.py's transposition table

        self.history = [self.zobrist_hash]       # initialize game history, detects 50-move rule and threefold repetition
    
    # sets the initial index for each piece on the board
    def initialize_piece_lists(self):
        for index, piece in enumerate(self.board):
            if piece != '#' and piece != -1:
                self.piece_lists[piece].append(index)

    def compute_hash(self):                      # computes a Zobrist hash based on global Zobrist tables
        hash = 0        # start at 0, updated with XORs

        # STEP 1: piece updates
        for piece_type in self.piece_lists:
            for sq_index in self.piece_lists[piece_type]:
                outer_index = TO_64[sq_index]
                inner_index = PIECE_CODES[piece_type]
                hash ^= ZOBRIST_PIECE_KEYS[outer_index][inner_index]    # update hash

        # STEP 2: castling right updates
        index_code = self.get_castle_rights_code()
        hash ^= ZOBRIST_CASTLING_KEYS[index_code]           # update hash

        # STEP 3: en passant updates
        if self.en_passant_square:
            ep_square = TO_64[self.en_passant_square]
            ep_file = ep_square % 8     # for 0 to 7
            hash ^= ZOBRIST_EP_KEYS[ep_file]

        # STEP 4: color to play updates
        hash ^= ZOBRIST_COLOR_KEY       # XOR regardless of color to toggle hash at each ply

        return hash
    
    # helper function to map each castling right combination to a Zobrist index code from 0-15 using bitwise OR
    def get_castle_rights_code(self):
        index_code = 0

        if self.white_castle_kingside: index_code |= 1      # set bit 0
        if self.white_castle_queenside: index_code |= 2     # set bit 1
        if self.black_castle_kingside: index_code |= 4      # set bit 2
        if self.black_castle_queenside: index_code |= 8     # set bit 3

        return index_code
        
    # move is a Move object containing necessary informaton for making the move
    def make_move(self, move):
        moving_piece = move.moving_piece
        piece_captured = move.piece_captured
        
        # MAKE THE MOVE, UPDATE PIECE LISTS / ZOBRIST HASH
        if (not move.is_en_passant) and (not move.is_castle): # if not a special move
            # make the move
            self.board[move.source_index] = '#'
            self.board[move.destination_index] = moving_piece

            self.zobrist_hash ^= ZOBRIST_PIECE_KEYS[TO_64[move.source_index]][PIECE_CODES[moving_piece]]
            
            self.piece_lists[moving_piece].remove(move.source_index)
            
            # remove the captured piece (if any) from its piece list and XOR it out of hash
            if piece_captured:
                self.piece_lists[piece_captured].remove(move.destination_index)
                self.zobrist_hash ^= ZOBRIST_PIECE_KEYS[TO_64[move.destination_index]][PIECE_CODES[move.piece_captured]]    

            if move.promotion_piece: # if this is a promotion
                self.board[move.destination_index] = move.promotion_piece
                self.piece_lists[move.promotion_piece].append(move.destination_index) 
                self.zobrist_hash ^= ZOBRIST_PIECE_KEYS[TO_64[move.destination_index]][PIECE_CODES[move.promotion_piece]]
            else:
                self.piece_lists[moving_piece].append(move.destination_index)         # add dest index to moving piece list
                self.zobrist_hash ^= ZOBRIST_PIECE_KEYS[TO_64[move.destination_index]][PIECE_CODES[moving_piece]] 
                    
        elif move.is_en_passant: # if move was en passant
            self.board[move.source_index] = '#'
            self.board[move.destination_index] = moving_piece
            
            self.piece_lists[moving_piece].remove(move.source_index)
            self.piece_lists[moving_piece].append(move.destination_index)

            self.zobrist_hash ^= ZOBRIST_PIECE_KEYS[TO_64[move.source_index]][PIECE_CODES[moving_piece]]
            self.zobrist_hash ^= ZOBRIST_PIECE_KEYS[TO_64[move.destination_index]][PIECE_CODES[moving_piece]]
            
            if self.color_to_play == 'white':                          # remove captured pawn
                self.board[move.destination_index + 10] = '#'          # destination_index = previous en_passant_square val
                self.piece_lists[piece_captured].remove(move.destination_index + 10)
                self.zobrist_hash ^= ZOBRIST_PIECE_KEYS[TO_64[move.destination_index + 10]][PIECE_CODES[move.piece_captured]]
            else:
                self.board[move.destination_index - 10] = '#'          # destination_index = previous en_passant_square val
                self.piece_lists[piece_captured].remove(move.destination_index - 10)
                self.zobrist_hash ^= ZOBRIST_PIECE_KEYS[TO_64[move.destination_index - 10]][PIECE_CODES[move.piece_captured]]
            
        # for castling moves move.destination_index will be the king's final square and is_castle flag will be True    
        elif move.is_castle:                                        # if move was to castle
            if move.destination_index == 97:                        # if white is castling kingside
                # move king to g1
                self.board[move.destination_index] = 'K'            
                self.piece_lists['K'].append(move.destination_index)
                self.zobrist_hash ^= ZOBRIST_PIECE_KEYS[TO_64[move.destination_index]][PIECE_CODES['K']]
                # remove king from home square
                self.board[move.source_index] = '#'                 
                self.piece_lists['K'].remove(move.source_index)
                self.zobrist_hash ^= ZOBRIST_PIECE_KEYS[TO_64[move.source_index]][PIECE_CODES['K']]
                # remove rook from h1
                self.board[98] = '#'
                self.piece_lists['R'].remove(98)
                self.zobrist_hash ^= ZOBRIST_PIECE_KEYS[TO_64[98]][PIECE_CODES['R']]
                # bring rook f1
                self.board[96] = 'R'                                
                self.piece_lists['R'].append(96)
                self.zobrist_hash ^= ZOBRIST_PIECE_KEYS[TO_64[96]][PIECE_CODES['R']]
                
            elif move.destination_index == 93:                      # if white is castling queenside
                # move king to c1
                self.board[move.destination_index] = 'K'    
                self.piece_lists['K'].append(move.destination_index)
                self.zobrist_hash ^= ZOBRIST_PIECE_KEYS[TO_64[move.destination_index]][PIECE_CODES['K']]
                # remove king from home square
                self.board[move.source_index] = '#'
                self.piece_lists['K'].remove(move.source_index)
                self.zobrist_hash ^= ZOBRIST_PIECE_KEYS[TO_64[move.source_index]][PIECE_CODES['K']]
                # remove rook from a1
                self.board[91] = '#'   
                self.piece_lists['R'].remove(91)
                self.zobrist_hash ^= ZOBRIST_PIECE_KEYS[TO_64[91]][PIECE_CODES['R']]
                # bring rook to d1
                self.board[94] = 'R'    
                self.piece_lists['R'].append(94)
                self.zobrist_hash ^= ZOBRIST_PIECE_KEYS[TO_64[94]][PIECE_CODES['R']]
                
            elif move.destination_index == 27:                      # if black is castling kingside
                # move king to g8
                self.board[move.destination_index] = 'k'
                self.piece_lists['k'].append(move.destination_index)
                self.zobrist_hash ^= ZOBRIST_PIECE_KEYS[TO_64[move.destination_index]][PIECE_CODES['k']]
                # remove king from home square
                self.board[move.source_index] = '#'
                self.piece_lists['k'].remove(move.source_index)
                self.zobrist_hash ^= ZOBRIST_PIECE_KEYS[TO_64[move.source_index]][PIECE_CODES['k']]
                # remove rook from h8
                self.board[28] = '#'
                self.piece_lists['r'].remove(28)
                self.zobrist_hash ^= ZOBRIST_PIECE_KEYS[TO_64[28]][PIECE_CODES['r']]
                # bring rook to f8
                self.board[26] = 'r'
                self.piece_lists['r'].append(26)
                self.zobrist_hash ^= ZOBRIST_PIECE_KEYS[TO_64[26]][PIECE_CODES['r']]
                
            elif move.destination_index == 23:                      # if black is castling queenside
                # move king to c8
                self.board[move.destination_index] = 'k'
                self.piece_lists['k'].append(move.destination_index)
                self.zobrist_hash ^= ZOBRIST_PIECE_KEYS[TO_64[move.destination_index]][PIECE_CODES['k']]
                # remove king from home square
                self.board[move.source_index] = '#'
                self.piece_lists['k'].remove(move.source_index)
                self.zobrist_hash ^= ZOBRIST_PIECE_KEYS[TO_64[move.source_index]][PIECE_CODES['k']]
                # remove rook from a8
                self.board[21] = '#'
                self.piece_lists['r'].remove(21)
                self.zobrist_hash ^= ZOBRIST_PIECE_KEYS[TO_64[21]][PIECE_CODES['r']]
                # bring rook to d8
                self.board[24] = 'r'
                self.piece_lists['r'].append(24)
                self.zobrist_hash ^= ZOBRIST_PIECE_KEYS[TO_64[24]][PIECE_CODES['r']]
        
        # UPDATE GAME STATE VALUES
        self.ply += 1
        
        # update color_to_play
        if self.color_to_play == 'white':
            self.color_to_play = 'black'
        else:
            self.color_to_play = 'white'
        self.zobrist_hash ^= ZOBRIST_COLOR_KEY      # toggle color to play in Zobrist hash
        
        # update 50-move-rule counter
        if moving_piece.lower() == 'p' or move.piece_captured != None:            # if a pawn move or capture
            self.half_move = 0    
        else:
            self.half_move += 1
        
        # reset en passant square 
        # first, XOR-out the old en passant square from Zobrist hash
        if self.en_passant_square:
            ep_square = TO_64[self.en_passant_square]
            ep_file = ep_square % 8     # for 0 to 7
            self.zobrist_hash ^= ZOBRIST_EP_KEYS[ep_file]

        self.en_passant_square = None                                             # null by default
        if moving_piece == 'P':                                                   # if white pawn moved
            if move.source_index >= 81 and move.source_index <= 88:               # if pawn started on home square
                if move.destination_index >= 61 and move.destination_index <= 68: # if pawn made 2-square advance
                    self.en_passant_square = move.destination_index + 10          # en passant target 1 square below dest

        elif moving_piece == 'p':                                                 # if black pawn moved
            if move.source_index >= 31 and move.source_index <= 38:               # if pawn started on home square
                if move.destination_index >= 51 and move.destination_index <= 58: # if pawn made 2-square advance
                    self.en_passant_square = move.destination_index - 10          # en passant target 1 square above dest

        # XOR-in new en passant square to Zobrist hash
        if self.en_passant_square:
            ep_square = TO_64[self.en_passant_square]
            ep_file = ep_square % 8     # for 0 to 7
            self.zobrist_hash ^= ZOBRIST_EP_KEYS[ep_file]
                    
        # reset castling rights
        # first, XOR-out the current castle rights from Zobrist hash
        index_code = self.get_castle_rights_code()
        self.zobrist_hash ^= ZOBRIST_CASTLING_KEYS[index_code]

        if move.is_castle:                                      # if the move was to castle
            if moving_piece == 'K':                             # if white castled
                self.white_castle_kingside = False
                self.white_castle_queenside = False
            elif moving_piece == 'k':                           # if black castled
                self.black_castle_kingside = False
                self.black_castle_queenside = False
        else:                                                   # if the move wasn't to castle
            if moving_piece == 'K':                             # if white moved their king
                self.white_castle_kingside = False
                self.white_castle_queenside = False
            if moving_piece == 'k':                             # if black moved their king
                self.black_castle_kingside = False
                self.black_castle_queenside = False
            if self.board[98] != "R":                           # if h1 square is not a white rook
                self.white_castle_kingside = False              
            if self.board[91] != "R":                           # if a1 square is not a white rook
                self.white_castle_queenside = False             
            if self.board[28] != "r":                           # if h8 square is not a black rook
                self.black_castle_kingside = False              
            if self.board[21] != "r":                           # if a8 square is not a black rook
                self.black_castle_queenside = False   
        
        # XOR-in the current castle rights to Zobrist hash
        index_code = self.get_castle_rights_code()
        self.zobrist_hash ^= ZOBRIST_CASTLING_KEYS[index_code]

        # add new position to the game history list
        self.history.append(self.zobrist_hash)
            
    # move is a Move object containing necessary information for unmaking the move
    def unmake_move(self, move):
        moved_piece = move.moving_piece
        
        # UNMAKE THE MOVE
        if (not move.is_en_passant) and (not move.is_castle):           # if not a special move 
            self.board[move.source_index] = moved_piece                 # return moved_piece to source index
            self.piece_lists[moved_piece].append(move.source_index)
            
            if move.piece_captured == None:
                self.board[move.destination_index] = '#'
            else:
                self.board[move.destination_index] = move.piece_captured
                self.piece_lists[move.piece_captured].append(move.destination_index)
            
            # remove the promotion square from the promoted piece's index list (if applicable)
            if move.promotion_piece:
                self.piece_lists[move.promotion_piece].remove(move.destination_index)
            else:
                self.piece_lists[moved_piece].remove(move.destination_index)
        
        elif move.is_en_passant:                                        # if the move was an en passant capture
            self.board[move.source_index] = moved_piece
            self.board[move.destination_index] = '#'
            self.piece_lists[moved_piece].append(move.source_index)
            self.piece_lists[moved_piece].remove(move.destination_index)

            if moved_piece == 'P':                                      # if white made the capture
                self.board[move.destination_index + 10] = 'p'           # return black pawn on en passant square
                self.piece_lists[move.piece_captured].append(move.destination_index + 10)
            else:                                                       # if black made the capture
                self.board[move.destination_index - 10] = 'P'           # return white pawn on en passant square
                self.piece_lists[move.piece_captured].append(move.destination_index - 10)
        
        # destination_index for castles marks the king's landing square
        elif move.is_castle:                                            # if the move was to castle
            if move.destination_index == 97:                            # if white castled kingside
                # remove king from g1
                self.board[move.destination_index] = '#'         
                self.piece_lists['K'].remove(move.destination_index)
                # remove rook from f1
                self.board[96] = '#'  
                self.piece_lists['R'].remove(96)
                # return king to e1
                self.board[95] = 'K' 
                self.piece_lists['K'].append(95)
                # return rook to h1
                self.board[98] = 'R'
                self.piece_lists['R'].append(98)

            elif move.destination_index == 93:                          # if white castled queenside
                # remove king from c1                        
                self.board[move.destination_index] = '#'  
                self.piece_lists['K'].remove(move.destination_index)
                # remove rook from d1
                self.board[94] = '#'  
                self.piece_lists['R'].remove(94)
                # return king to e1
                self.board[95] = 'K' 
                self.piece_lists['K'].append(95)
                # return rook to a1
                self.board[91] = 'R'
                self.piece_lists['R'].append(91)

            elif move.destination_index == 27:                          # if black castled kingside
                # remove king from g8
                self.board[move.destination_index] = '#'     
                self.piece_lists['k'].remove(move.destination_index)
                # remove rook from f8
                self.board[26] = '#'   
                self.piece_lists['r'].remove(26)
                # return king to e8
                self.board[25] = 'k' 
                self.piece_lists['k'].append(25)
                # return rook to h8
                self.board[28] = 'r'     
                self.piece_lists['r'].append(28)

            elif move.destination_index == 23:                          # if black castled queenside
                # remove king from c8
                self.board[move.destination_index] = '#'         
                self.piece_lists['k'].remove(move.destination_index)
                # remove rook from d8
                self.board[24] = '#' 
                self.piece_lists['r'].remove(24)
                # return king to e8
                self.board[25] = 'k' 
                self.piece_lists['k'].append(25)
                # return rook to a8
                self.board[21] = 'r'
                self.piece_lists['r'].append(21)
        
        # RESTORE PREVIOUS GAME STATE VARIABLES
        self.ply -= 1

        # revert color to play
        self.color_to_play = move.previous_color_to_play

        self.half_move = move.previous_half_move                    # revert 50 move rule counter
        self.en_passant_square = move.previous_en_passant_square    # revert en passant square

        # revert castling rights
        self.white_castle_kingside = move.previous_white_castle_kingside
        self.white_castle_queenside = move.previous_white_castle_queenside
        self.black_castle_kingside = move.previous_black_castle_kingside
        self.black_castle_queenside = move.previous_black_castle_queenside

        # revert Zobrist hash
        self.zobrist_hash = move.previous_zobrist_hash

        # revert updates to the game history list
        self.history.pop()
    
    def fifty_move_criteria_met(self):      # checks if criteria for fifty move rule have been met
        return self.half_move == 100

    # used to make a copy of the current board before starting a search
    # this is necessary to prevent iterative deepening time cap from abruptly preventing move reversal
    def copy(self):
        new_board = Board()

        # Copy all attributes
        new_board.board = self.board[:]
        new_board.color_to_play = self.color_to_play
        new_board.white_castle_kingside = self.white_castle_kingside
        new_board.white_castle_queenside = self.white_castle_queenside
        new_board.black_castle_kingside = self.black_castle_kingside
        new_board.black_castle_queenside = self.black_castle_queenside
        new_board.half_move = self.half_move
        new_board.ply = self.ply
        new_board.en_passant_square = self.en_passant_square
        new_board.zobrist_hash = self.zobrist_hash
        new_board.history = self.history[:]
        
        # Deepcopy the piece_lists dictionary
        new_board.piece_lists = copy.deepcopy(self.piece_lists)
        
        return new_board

    # checks if the current position is a repetition
    # a repetition is classified as a position at least once since the last irreversible (pawn or capture) move
    def is_repetition(self):
        # relevant history starts from the ply of the last irreversible move
        lookback_start_index = max(0, self.ply - self.half_move)

        # search the relevant game history for a matching Zobrist key
        for i in range(lookback_start_index, self.ply):
            if self.history[i] == self.zobrist_hash:
                return True
        
        return False
    
# acts as a "time capsule", capturing a game state snapshot for complete move execution and reversal
# used by generate_moves() during move validation and minimax() during game tree search
class Move:
    def __init__(
            self, position, moving_piece, source_index, destination_index, 
            piece_captured, is_en_passant, is_castle, promotion_piece=None
        ):
        # basic move information for making and unmaking
        self.moving_piece = moving_piece
        self.source_index = source_index
        self.destination_index = destination_index
        self.piece_captured = piece_captured
        
        # special move flags
        self.is_en_passant = is_en_passant
        self.is_castle = is_castle
        self.promotion_piece = promotion_piece
        
        # capture previous special move values for unmaking moves
        self.previous_white_castle_kingside = position.white_castle_kingside
        self.previous_white_castle_queenside = position.white_castle_queenside
        self.previous_black_castle_kingside = position.black_castle_kingside
        self.previous_black_castle_queenside = position.black_castle_queenside
        self.previous_en_passant_square = position.en_passant_square
        self.previous_half_move = position.half_move
        self.previous_color_to_play = position.color_to_play
        self.previous_zobrist_hash = position.zobrist_hash