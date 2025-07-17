# chess-engine

A classic chess engine written in Python, using a minimax search algorithm with alpha-beta pruning. This project is built from the ground up with a focus on a clean, modular design.

## Key Features

- **Search Algorithm**: Implements a classic minimax search with alpha-beta pruning to efficiently explore the game tree.
- **Reversible Moves**: Features a fully reversible `make_move`/`unmake_move` system, substantially improving search performance by removing the need for array copying operations.
- **Efficient Board Representation**: Uses a 1D 10x12 "Mailbox" array with sentry squares to optimize move generation and eliminate performance bottlenecks with constant bounds-checking.
- **Complete Rule Set**: Designed to handle all standard chess rules, including special moves like castling and en passant.
- **Object-Oriented Design**: Utilizes `Board` and `Move` classes to create a robust and maintainable representation of the game state.

## Project Structure

The engine is organized into distinct modules, each representing a core subsystem:
- **`main.py`**: The main entry point for running the application or starting an API server.
- **`engine.py`**: Contains minimax and alpha-beta pruning search logic.
- **`board.py`**: Defines the core data structures: `Board` and `Move`.
- **`move_generator.py`**: Responsible for generating all possible legal moves in a position.
- **`evaluation.py`**: Contains the logic for statically evaluating a board position.