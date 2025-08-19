# Python Chess Engine

## Table of Contents
- [Overview](#overview)
- [Key Stats](#key-stats)
- [Features](#features)
- [Installation & Usage](#installation--usage)

## Overview
A feature-rich chess engine written in Python. This project is built from the ground-up with a focus on a clean, modular design and serves as a strong foundation in chess engine development.

## Key Stats
- **Estimated Elo**: 1700-1800 blitz (chess.com)
- **Performance**: ~1.5-2 million nodes/second (with PyPy)
- **Validated**: Passes perft tests for move generation, including the Kiwipete position up to depth 5.

## Features

### Search Algorithm
The engine's search algorithm revolves around a minimax + alpha-beta pruning core search, and layers on a suite of modern, powerful optimizations to maximize the efficiency of game tree exploration.

-   **Iterative Deepening**: Enables effective time management and improves move ordering in subsequent searches.
-   **Principal Variation Search (PVS)**: A powerful optimization over standard alpha-beta that uses tight null-window searches to prune the search tree more efficiently.
-   **Move Ordering**: Sorts moves to maximize alpha-beta pruning effectiveness using a carefully tuned hierarchy:
    1.  Principal Variation / Previous Best Move
    2.  Hash Move (from Transposition Table)
    3.  MVV-LVA (Most Valuable Victim, Least Valuable Attacker) for captures
    4.  Killer Moves (quiet moves that caused cutoffs at the same ply)
    5.  History Heuristic (quiet moves that have been successful in the past)
-   **Transposition Table**: Stores previously evaluated positions using Zobrist hashing to avoid re-searching identical game states.
-   **Quiescence Search**: Extends the search horizon for tactical positions, considering only captures and check-evasions, to ensure the final evaluation is stable and avoid the "horizon effect." The q-search uses its own MVV-LVA move-ordering, stand-pat pruning, and delta pruning.
-   **Late Move Reductions (LMR)**: Reduces search depth for less promising moves, directing computational resources to the principal variation.
-   **Futility Pruning**: Prunes shallow, quiet moves at nodes near the leaves that are highly unlikely to improve the current evaluation.
-   **Opening Book**: Uses a Polyglot (`.bin`) opening book (gm2001) for instant and reliable opening play.

### Board & Move Generation

-   **Board Representation**: A 10x12 "Mailbox" array with out-of-bounds sentinel squares to eliminate the need for bounds-checking during move generation.
-   **Piece Lists**: Provides fast, direct access to piece locations, avoiding costly full-board scans.
-   **Efficient Move Generation**: A three-stage pipeline (Threat Analysis -> Check/Pin Detection -> Validation) ensures fast and correct legal move generation.
-   **Reversible Moves**: Moves are made and reversed using the `make_move` and `unmake_move` methods. A "time capsule" `Move` object stores all necessary game state information, allowing for easy move reversal and eliminating the need for deep copying the board array.

### Evaluation Function

-   **Tapered Evaluation**: Smoothly interpolates between mid-game and endgame values based on the material left on the board.
-   **PeSTO's Piece-Square Tables**: Utilizes the well-regarded PSTs from the PeSTO engine for piece placement evaluation.
-   **Positional Heuristics**: Includes tapered bonuses and penalties for mobility, king safety (pawn shield, king attacks), central control, castling rights, and piece development.

## Installation & Usage

Follow these instructions to get the engine running on your local machine.

### Prerequisites

-   Python 3.x
-   **Recommended**: [PyPy3](https://www.pypy.org/download.html) for a significant performance boost (~5-10x faster).
-   The `python-chess` library for Polyglot opening book support.
    ```sh
    pip install python-chess
    ```

### Installation

1.  Clone the repository
2.  Download the `gm2001.bin` opening book and place it in the root directory of the project.

### Running the Engine

To play against the engine in the console, run `main.py`:

```sh
# Using standard Python
python main.py

# Using PyPy (recommended)
pypy3 main.py
```

Player color and engine thinking time can be configured by editing the variables at the bottom of the `main.py` file.