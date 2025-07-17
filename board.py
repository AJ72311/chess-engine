# -------------------------- BOARD AND MOVE CLASSES: BOARD REPRESENTATION, MAKING / UNMAKING MOVES --------------------------

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
        
    # move is a Move object containing necessary informaton for making the move
    def make_move(self, move):
        moving_piece = self.board[move.source_index]
        
        # MAKE THE MOVE
        if (not move.is_en_passant) and (not move.is_castle):               # if not a special move
            # make the move
            self.board[move.source_index] = '#'
            self.board[move.destination_index] = moving_piece
                    
        elif move.is_en_passant:                                            # if move was en passant
            self.board[move.source_index] = '#'
            self.board[move.destination_index] = moving_piece
            
            if self.color_to_play == 'white':                               # remove captured pawn
                self.board[move.destination_index + 10] = '#'               # destination_index = previous en_passant_square value
            else:
                self.board[move.destination_index - 10] = '#'               # destination_index = previous en_passant_square value
            
        # for castling moves move.destination_index will be the king's final square and is_castle flag will be True    
        elif move.is_castle:                                        # if move was to castle
            if move.destination_index == 97:                        # if white is castling kingside
                self.board[move.destination_index] = 'K'            # move king to g1
                self.board[move.source_index] = '#'                 # remove king from home square
                self.board[98] = '#'                                # remove rook from h1
                self.board[96] = 'R'                                # bring rook f1
            elif move.destination_index == 93:                      # if white is castling queenside
                self.board[move.destination_index] = 'K'            # move king to c1
                self.board[move.source_index] = '#'                 # remove king from home square
                self.board[91] = '#'                                # remove rook from a1
                self.board[94] = 'R'                                # bring rook to d1
            elif move.destination_index == 27:                      # if black is castling kingside
                self.board[move.destination_index] = 'k'            # move king to g8
                self.board[move.source_index] = '#'                 # remove king from home square
                self.board[28] = '#'                                # remove rook from h8
                self.board[26] = 'r'                                # bring rook f8
            elif move.destination_index == 23:                      # if black is castling queenside
                self.board[move.destination_index] = 'k'            # move king to c8
                self.board[move.source_index] = '#'                 # remove king from home square
                self.board[21] = '#'                                # remove rook from a8
                self.board[24] = 'r'                                # bring rook to d8
        
        # UPDATE GAME STATE VALUES
        self.ply += 1
        
        # update color_to_play
        if self.color_to_play == 'white':
            self.color_to_play = 'black'
        else:
            self.color_to_play = 'white'
        
        # update 50-move-rule counter
        if moving_piece.lower() == 'p' or move.piece_captured != None:              # if a pawn move or capture                        
            self.half_move = 0    
        else:
            self.half_move += 1
        
        # reset en passant square 
        self.en_passant_square = None                                                # null by default
        if moving_piece == 'P':                                                      # if white pawn moved
            if move.source_index >= 81 and move.source_index <= 88:                  # if pawn started on home square
                if move.destination_index >= 61 and move.destination_index <= 68:    # if pawn made 2-square advance
                    self.en_passant_square = move.destination_index + 10             # en passant target 1 square below destination

        elif moving_piece == 'p':                                                    # if black pawn moved
            if move.source_index >= 31 and move.source_index <= 38:                  # if pawn started on home square
                if move.destination_index >= 51 and move.destination_index <= 58:    # if pawn made 2-square advance
                    self.en_passant_square = move.destination_index - 10             # en passant target 1 square above destination
                    
        # reset castling rights
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
            
    # move is a Move object containing necessary information for unmaking the move
    def unmake_move(self, move):
        moved_piece = self.board[move.destination_index]
        
        # UNMAKE THE MOVE
        if (not move.is_en_passant) and (not move.is_castle):           # if not a special move 
            self.board[move.source_index] = moved_piece                 # return moved_piece to source index
            
            if move.piece_captured == None:
                self.board[move.destination_index] = '#'
            else:
                self.board[move.destination_index] = move.piece_captured
        
        elif move.is_en_passant:                                        # if the move was an en passant capture
            self.board[move.source_index] = moved_piece
            self.board[move.destination_index] = '#'

            if moved_piece == 'P':                                      # if white made the capture
                self.board[move.destination_index + 10] = 'p'           # return black pawn on en passant square
            else:                                                       # if black made the capture
                self.board[move.destination_index - 10] = 'P'           # return white pawn on en passant square
        
        # destination_index for castles marks the king's landing square
        elif move.is_castle:                                            # if the move was to castle
            if move.destination_index == 97:                            # if white castled kingside
                self.board[move.destination_index] = '#'                # remove king from g1
                self.board[96] = '#'                                    # remove rook from f1
                self.board[95] = 'K'                                    # return king to e1
                self.board[98] = 'R'                                    # return rook to h1
            elif move.destination_index == 93:                          # if white castled queenside
                self.board[move.destination_index] = '#'                # remove king from c1
                self.board[94] = '#'                                    # remove rook from d1
                self.board[95] = 'K'                                    # return king to e1
                self.board[91] = 'R'                                    # return rook to a1
            elif move.destination_index == 27:                          # if black castled kingside
                self.board[move.destination_index] = '#'                # remove king from g8
                self.board[26] = '#'                                    # remove rook from f8
                self.board[25] = 'k'                                    # return king to e8
                self.board[28] = 'r'                                    # return rook to h8
            elif move.destination_index == 23:                          # if black castled queenside
                self.board[move.destination_index] = '#'                # remove king from c8
                self.board[24] = '#'                                    # remove rook from d8
                self.board[25] = 'k'                                    # return king to e8
                self.board[21] = 'r'                                    # return rook to a8
        
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

    def is_checkmate(self):     # returns a boolean
        pass
    
    def is_stalemate(self):     # returns a boolean
        pass
    
    def fifty_move_criteria_met(self):      # checks if criteria for fifty move rule have been met
        return self.half_move == 100
    
# acts as a "time capsule", capturing a game state snapshot for complete move execution and reversal
# used by generate_moves() during move validation and minimax() during game tree search
class Move:
    def __init__(
        self, position, moving_piece, source_index, destination_index, piece_captured, is_en_passant, is_castle):
        # basic move information for making and unmaking
        self.moving_piece = moving_piece
        self.source_index = source_index
        self.destination_index = destination_index
        self.piece_captured = piece_captured
        
        # special move flags
        self.is_en_passant = is_en_passant
        self.is_castle = is_castle
        
        # capture previous special move values for unmaking moves
        self.previous_white_castle_kingside = position.white_castle_kingside
        self.previous_white_castle_queenside = position.white_castle_queenside
        self.previous_black_castle_kingside = position.black_castle_kingside
        self.previous_black_castle_queenside = position.black_castle_queenside
        self.previous_en_passant_square = position.en_passant_square
        self.previous_half_move = position.half_move
        self.previous_color_to_play = position.color_to_play