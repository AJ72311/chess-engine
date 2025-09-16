# Quieceros: A Python Chess Engine & Web Application

## Table of Contents
- [Overview](#overview)
- [Live Demo](#live-demo)
- [Key Stats](#key-stats)
- [The Engine: Quieceros](#the-engine-quieceros)
  - [Board Representation](#board-representation)
  - [Move Generation](#move-generation)
  - [Search Algorithm](#search-algorithm)
  - [Evaluation Function](#evaluation-function)
- [Application Architecture](#application-architecture)
  - [Tech Stack](#tech-stack)
  - [Architectural Overview](#architectural-overview)
- [About the Name](#about-the-name)
- [Installation & Local Usage](#installation--local-usage)

## Overview

Quieceros is a feature-rich chess engine built from the ground up using Python. The engine is served via a stateful, multi-process FastAPI backend and is playable through a React + TypeScript frontend. This project's core challenge was implementing advanced chess programming concepts within the limitations of an interpreted language, demanding sophisticated architectural patterns to achieve high performance.

## Live Demo

Play against Quieceros here: https://quieceros-chess.vercel.app

## Key Stats
- **Estimated Elo**: ~1700-1800 Chess.com blitz
- **Search Performance**: 50k-133k nodes/second (single-threaded, Apple M1 CPU)

## The Engine: Quieceros
Quieceros is the centerpiece of the project. It was designed with a focus on implementing a powerful suite of optimizations while navigating the unique performance challenges of an interpreted language.

### Board Representation
The engine utilizes a **10x12 Mailbox array** for its board representation, with out-of-bounds sentinel squares to eliminate the need for bounds-checking during move generation. An additional set of **Piece Lists** is maintained to allow O(1) access to piece indices, avoiding costly full-board scans. This representation was chosen over the conventionally-faster bitboard approach for a few key reasons:
    1. **High Overhead of Bitwise Operations**: Standard bitwise operations (scans, masks, shifts, etc.) are not nearly as well-optimized in Python as they are in compiled languages and carry significant overhead<br>  
    2. **Lack of Low-Level Optimizations**: Python doesn't support the low-level CPU intrinsics (`POPCNT`) and vectorized operations (`SIMD`) that make bitboards efficient in compiled languages<br>  
    3. **Highly Optimized Native Types**: Python's list/dict access is written in C and heavily optimized

These factors make the performance benefits of bitboards minimal in Python, while the complexity of implementing them remains high.

The game tree is traversed through the Board class's `make_move` and `unmake_move` methods. When a move is made, a lightweight "time capsule" `Move` object is created. This object stores a snapshot of non-board-array game state (Zobrist hash, castling rights, en passant square, etc.). The `unmake_move` method restores the prior game state variables using this snapshot and manually reverts the board array to avoid expensive deep-copying operations.

### Move Generation
A cornerstone of this engine's move generation algorithm is its **static legality checking**, where the legality of pseudo-legal moves is verified *without* making any `make_move` or `unmake_move` calls. The popular alternative to this is to employ a "make-test-unmake" cycle, where each pseudo-legal move is made on the board to test if it allows the king to be captured. While the make-test-unmake pattern is simpler, it incurs a prohibitive performance penalty in Python due to the interpreter's high function call overhead, making the static approach more favorable for this application.

The move generator follows a 3-stage pipeline:
    1. **Pseudo-Legal Move Generation**: Uses index deltas to generate all potential piece target squares
    2. **Threat & Pin Analysis**: Performs ray-walks from the king to detect any absolute pins on friendly pieces. An enemy threat map is also generated to count checks and identify illegal destination squares for the king
    3. **Validation**: Pseudo-legal moves generated in stage 1 are filtered against the pin and threat constraints identified in stage 2

### Search Algorithm
The search revolves around a fail-soft alpha-beta framework and layers on the following optimizations:
- **Principal Variation Search (PVS)**: Uses optimistic null-window searches for more aggressive pruning in non-PV nodes. If a null-window search fails high, a re-search is performed with a full window
- **Iterative Deepening**: Allows for effective time management and seeds subsequent, deeper searches with the best move found in previous iterations
- **Transposition Table**: A large hash table that stores previously evaluated positions using Zobrist hashing, dramatically reducing redundant branches
- **Move Ordering**: Uses a priority hierarchy to sort moves in order of descending likelihood of success, maximizing the efficiency of alpha-beta pruning. The order is:
    1. Principal Variation Move
    2. Hash Move
    3. MVV-LVA (Most Valuable Victim, Least Valuable Attacker) for captures
    4. Killer Moves (quiet moves that recently triggered beta cutoffs at the same ply)
    5. History Heuristic (quiet moves that have proven effective throughout the search)
- **Quiescence Search**: A specialized search initiated at leaf nodes of the full-width search that considers only captures and check-evasions. This ensures evaluations are stable and mitigates the notorious "horizon effect." It uses its own MVV-LVA move ordering, stand-pat pruning, and delta pruning
- **Late-Move Reductions (LMR)**: Reduces the search depth for moves that appear late in the ordered list to direct computational resources toward the principal variation
- **Extended Futility Pruning**: Aggressively prunes quiet moves at frontier and pre-frontier nodes that are beneath the current alpha-score by a set margin
- **Opening Book**: Employs the `gm2001.bin` Polyglot opening book for fast and reliable opening play

### Evaluation Function
The static evaluation starts with a baseline material count and makes adjustments based on the following factors:
- **PeSTO's Piece-Square Tables**: A well-regarded set of phased PSTs. The current game phase is used to interpolate a value between midgame and endgame tables
- **Positional Heuristics**: Includes tapered bonuses and penalties for piece mobility, king safety (pawn shield, nearby attacks), central control, castling rights, and piece development

## Application Architecture

### Tech Stack
- **Engine & Backend**: Python 3, PyPy3, FastAPI, Uvicorn, Gunicorn, Nginx
- **Frontend**: React, TypeScript, Vite, Axios, `react-chessboard`

### Architectural Overview
The application uses a decoupled architecture.
- The **Frontend** is a lightweight, static single-page application (SPA) built with React and TypeScript.
- The **Backend** employs a **stateful, multi-process worker architecture**. A lightweight, non-blocking FastAPI dispatcher receives requests and forwards them to one of several persistent worker processes via `multiprocessing` Queues. Each worker maintains the state for its assigned games in its own memory, bypassing Python's Global Interpreter Lock (GIL) and eliminating data serialization bottlenecks during inter-process communication. The dispatcher assigns new sessions to the least-busy worker to avoid over-saturation of a single core. This design allows for true parallel execution of simultaneous searches.
- An **Nginx** reverse proxy is deployed in front of the backend application server to handle SSL/TLS termination, connection management, and security hardening.

## About the Name

The name "Quieceros" pays homage to **Quiescence Search**, the most impactful optimization made to the engine. This selective search extension transformed Quieceros and was a turning point in the project, instantly yielding a stunning rise in playing strength and even allowing for search depth to be lowered for faster moves while still improving tactical accuracy. This served as a textbook demonstration of the crippling impact the horizon effect has on tactical stability and the profound gains unlocked by its mitigation.

## Installation & Local Usage

Follow these instructions to get the full application running on your local machine.

### Prerequisites
- **Backend**: [PyPy3](https://www.pypy.org/download.html) is strongly recommended for performance.
- **Frontend**: [Node.js](https://nodejs.org/en) and `npm` (or `yarn`).

### Installation
1.  **Clone the Repository**:
    ```sh
    git clone https://github.com/AJ72311/chess-engine.git
    cd chess-engine
    ```
2.  **Download the Opening Book (Optional)**:
    - The engine uses the `gm2001.bin` Polyglot opening book. Download it and place it in the root directory of the project.
3.  **Backend Setup**:
    - Create a virtual environment and install dependencies:
      ```sh
      pypy3 -m venv venv
      source venv/bin/activate
      pypy3 -m pip install -r requirements.txt
      ```
    - Create a local `.env` file in the project root. You can copy the example:
      ```sh
      cp .env.example .env
      ```
4.  **Frontend Setup**:
    - Navigate to the frontend directory and install dependencies:
      ```sh
      cd frontend
      npm install
      ```
    - Create a local development `.env` file. You can copy the example:
      ```sh
      cp .env.development.example .env.development
      ```

### Running Locally
You will need to run the backend and frontend in two separate terminal sessions.

1.  **Start the Backend API Server**:
    - From the project's root directory:
      ```sh
      source venv/bin/activate
      pypy3 -m uvicorn main:app --reload
      ```
    - The API will be available at `http://127.0.0.1:8000`.

2.  **Start the Frontend Development Server**:
    - From the `frontend/` directory:
      ```sh
      npm run dev
      ```
    - The web application will be available at `http://localhost:5173`.

> **Note**: A command-line interface for playing against the engine is available for testing and debugging purposes. It can be run with `pypy3 cli.py` within the backend directory. Additionally, the Search class's iterative deepening wrapper includes commented-out debug prints that display the evaluation of root-level nodes at each depth.