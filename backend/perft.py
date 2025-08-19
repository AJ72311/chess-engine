import time
from board import Move, Board
from move_generator import generate_moves
from utils import INDEX_TO_ALGEBRAIC, ALGEBRAIC_TO_INDEX, move_to_algebraic, board_to_fen, set_board_from_fen


# recursively calcuates the number of leaf nodes at a given depth
def perft(board, depth):
    # base case, if depth is 0 we are at a leaf node, return 1 to count it
    if depth == 0:
        return 1
    
    nodes = 0       # initialize nodes resulting from the current position's game tree
    legal_moves = generate_moves(board)[0]

    for move in legal_moves:
        board.make_move(move)
        nodes += perft(board, depth - 1) # recursive call, add total nodes resulting from move's game sub-tree to nodes
        board.unmake_move(move)

    return nodes

# runs a perft test to a set depth for each move possible in a given position
def divide(board, depth):
    if depth <= 0:
        print('Depth must be greater than 0 for a divide')
        return

    print(f'--- Divide for Depth {depth} ---')
    print(f"--- FEN: {board_to_fen(board)} ---")

    # log start time for speed performance testing
    start_time = time.time()

    total_nodes = 0
    legal_moves = generate_moves(board)[0]

    # sort move list for consistent output, streamlined comparison against established results
    sorted_moves = sorted(legal_moves, key=lambda m: (m.source_index, m.destination_index))

    for move in sorted_moves:
        board.make_move(move)
        nodes = perft(board, depth - 1)
        total_nodes += nodes
        board.unmake_move(move)
        print(f'{move_to_algebraic(move)}: {nodes}')

    # log end and elapsed time for speed performance testing
    end_time = time.time()
    elapsed_time = end_time - start_time
    nodes_per_second = total_nodes / elapsed_time if elapsed_time > 0 else 0

    print('\n--- Summary ---')
    print(f'Total Moves: {len(legal_moves)}')
    print(f'Total Nodes: {total_nodes}')
    print(f'Elapsed Time: {elapsed_time:.4f} seconds')
    print(f'Nodes per Second: {nodes_per_second:,.2f}')

if __name__ == '__main__':
    TEST_DEPTH = 5                  # depth to serach during tests
    test_board = Board()            # create a board object for testing, represents the starting position 

    FEN_STRING = 'r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1' # sets custom initial board position

    if FEN_STRING:
        set_board_from_fen(test_board, FEN_STRING)

    divide(test_board, TEST_DEPTH)  # run the test