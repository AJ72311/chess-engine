import { useState, useRef, useCallback, type CSSProperties, useEffect } from 'react';
import { Chessboard } from 'react-chessboard';
import { Chess, type Square } from 'chess.js';
import styles from './Game.module.css';
import axios from 'axios';
import Odometer from 'react-odometerjs';
import 'odometer/themes/odometer-theme-default.css';
import cogUrl from '../../assets/cog.svg?url'

type SquareStyles = Partial<Record<Square, CSSProperties>>;

function Game() {
    // create a chess.js instance using ref to maintain game state across renders
    const chessGameRef = useRef(new Chess());
    const chessGame = chessGameRef.current;

    // track current position FEN in state to trigger re-renders
    const [boardPosition, setBoardPosition] = useState<string>(chessGame.fen());
    
    // used for showing move options and highlights when clicking on a piece
    const [moveFrom, setMoveFrom] = useState<string>('');
    const [optionSquares, setOptionSquares] = useState<object>({});
    const [checkHighlight, setCheckHighlight] = useState<object>({});
    const [lastMoveHighlight, setLastMoveHighlight] = useState<object>({});

    // used to track the session with the engine's api
    const [sessionID, setSessionID] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [countdown, setCountdown] = useState<number>(0);
    const [positionsSearched, setPositionsSearched] = useState<number>(0);
    const [depthSearched, setDepthSearched] = useState<number>(0);

    // gets the engine's response to a player's move, returns updated FEN with engine stats
    const handleMove = useCallback(async (playerMove: string) => {
        try {
            if (!sessionID) {
                const response = await axios.post('/game/new-game', {
                    player_move: playerMove,
                });

                const newFEN = response.data.new_fen;  // updated FEN
                const gameID = response.data.game_id;  // sessionID
                const movePlayed = response.data.move_played;
                const depthReached = response.data.depth_reached;
                const nodesSearched = response.data.nodes_searched;

                setBoardPosition(newFEN);
                setLastMoveHighlight(highlightFromUCI(movePlayed));
                setPositionsSearched(nodesSearched);
                setDepthSearched(depthReached);

                chessGame.load(newFEN);
                setSessionID(gameID);
            
            } else {
                const response = await axios.post('/game/play-move', {
                    player_move: playerMove,
                    session_id: sessionID,
                    client_fen: boardPosition,
                });

                const newFEN = response.data.new_fen;
                const movePlayed = response.data.move_played;
                const depthReached = response.data.depth_reached;
                const nodesSearched = response.data.nodes_searched;

                setLastMoveHighlight(highlightFromUCI(movePlayed));
                setPositionsSearched(nodesSearched);
                setDepthSearched(depthReached);

                chessGame.load(newFEN);
                setBoardPosition(newFEN);
            }
        
        } catch (error) {
            throw error;
        }
    }, [sessionID, boardPosition]);

    // helper function for useEffect, finds king index to highlight in red for checks
    function findKingSquare(color: 'w' | 'b'): Square {
        const board = chessGame.board();
        const files = 'abcdefgh';
        for (let r = 0; r < 8; r++) {
            for (let f = 0; f < 8; f++) {
                const p = board[r][f];
                if (p?.type === 'k' && p.color === color) {
                    return (files[f] + (8 - r)) as Square;
                }
            }
        }
        throw new Error('King not found');
    }

    // runs upon a new move, highlights king square to red if in check
    useEffect(() => {
        if (chessGame.inCheck()) {
            const kingSq = findKingSquare(chessGame.turn());
            setCheckHighlight({
                [kingSq]: {
                    background: 'rgba(235, 120, 120, 1)',
                }
            });
        } else {
            // not in check, clear highlight
            setCheckHighlight({});
        }
        }, [boardPosition]); 

    // runs upon a new move, sets the engine move countdown timer
    useEffect(() => {
        if (!isLoading) {
            setCountdown(0);
            return;
        }

        setCountdown(5);
        const timer = setInterval(() => {
            setCountdown(c => {
                if (c <= 1) {
                    clearInterval(timer);
                    return 0;
                }
                return c - 1;
            });
        }, 1000);

        return () => clearInterval(timer);
    }, [isLoading]);

    // helper function, determines if the piece clicked has valid moves
    function getMoveOptions(square: Square): boolean {
        // get moves for the square
        const moves = chessGame.moves({
            square,
            verbose: true,
        });

        // if no valid moves, return false
        if (moves.length === 0) {
            setOptionSquares({});
            return false;
        }

        // create object to hold valid squares
        const newSquares: Record<string, React.CSSProperties> = {};

        // loop through moves and set option squares
        for (const move of moves) {
            newSquares[move.to] = {
                background: chessGame.get(move.to) &&
                chessGame.get(move.to)?.color !== 
                chessGame.get(square)?.color ? 
                'radial-gradient(circle, rgba(0,0,0,.1) 85%, transparent 85%)' : // big circle if capture
                'radial-gradient(circle, rgba(0,0,0,.1) 25%, transparent 25%)',

                // smaller circle for non-captures
                borderRadius: '50%'
            };
        }

        // highlight the square to be departed
        newSquares[square] = {
            background: 'rgba(246, 164, 64, 0.5)',
        };

        setOptionSquares(newSquares);
        return true;
    }

    // helper function, helps highlight the most recently played move
    function highlightFromUCI(move: string): SquareStyles {
        const from = move.slice(0,2) as Square;
        const to   = move.slice(2,4) as Square;
        return {
            [from]: { background: 'rgba(246, 164, 64, 0.5)' },  // blue for “from”
            [to]:   { background: 'rgba(246, 164, 64, 0.5)' }   // green for “to”
        };
    }

    const onDragBegin = useCallback((_piece: string, source: Square) => {
        // get all legal moves from this square
        const moves = chessGame.moves({ square: source, verbose: true });
        
        // build a styles object for each target square and the source square
        const styles: SquareStyles = {};
        // highlight the departing square in yellow
        styles[source] = { background: 'rgba(246, 164, 64, 0.5)' };

        // show dots on target squares
        moves.forEach(move => {
            styles[move.to] = {
                background: chessGame.get(move.to) &&
                chessGame.get(move.to)?.color !== 
                chessGame.get(source)?.color ? 
                'radial-gradient(circle, rgba(0,0,0,.1) 60%, transparent 60%)' : // big circle if capture
                'radial-gradient(circle, rgba(0,0,0,.1) 25%, transparent 25%)',

                // smaller circle for non-captures
                borderRadius: '50%'
            };
        });

        setOptionSquares(styles);
    }, [chessGame]);

    // validates dragging moves
    const onDrop = useCallback((sourceSqr: string, destinationSqr: string): boolean => {
        // return false if target square is null (from piece being dropped off the board)
        if (!destinationSqr) return false;

        // try making the move according to chess.js logic
        try {
            const result = chessGame.move({
                from: sourceSqr,
                to: destinationSqr,
                promotion: 'q', // always promote to queen for simplicity
            });

            // if the move succeeded
            setBoardPosition(chessGame.fen());
            setLastMoveHighlight(highlightFromUCI(`${sourceSqr}${destinationSqr}${result.promotion??''}`));

            // post to api
            setIsLoading(true);
            handleMove(`${sourceSqr}${destinationSqr}${result.promotion ?? ''}`)
            .catch(() => {
                chessGame.undo(); // if server problem, roll back locally
                setBoardPosition(chessGame.fen());
            })
            .finally(() => setIsLoading(false));

            return true;
        
        } catch {
            // if the move failed
            return false;
        }
    }, [chessGame, handleMove]);

    const onDragEnd = useCallback(() => {
        // user released outside valid square or cancelled drag, reset valid move options
        setOptionSquares({});
    }, []);

    // validates clicking moves
    const onSqrClick = useCallback((square: string): void => {
        // if user reclicked the same square again, clear and return
        if (moveFrom === square) {
            setMoveFrom('');
            setOptionSquares({});
            return;
        }

        // if a square to be departed hasn't been set yet, generate valid moves
        if (!moveFrom) {
            const hasMoveOptions = getMoveOptions(square as Square);

            // if there are valid move options, set the moveFrom square
            if (hasMoveOptions) {
                setMoveFrom(square);
            }

            return;
        }

        // if a square to be departed has already been set, try to make the move
        const moves = chessGame.moves({
            square: moveFrom as Square,
            verbose: true,
        });
        const foundMove = moves.find(m => m.from === moveFrom && m.to === square);

        // if not a valid move
        if (!foundMove) {
            const hasMoveOptions = getMoveOptions(square as Square);

            // if new piece, setMoveFrom, otherwise clear moveFrom
            setMoveFrom(hasMoveOptions ? square : '');

            return; // return early for invalid moves
        }

        // if valid move, check for legality
        try {
            const result = chessGame.move({
                from: moveFrom,
                to: square,
                promotion: 'q', // always promote to queen for simplicity
            });

            // if move succeeded, clear and return
            setBoardPosition(chessGame.fen());
            setLastMoveHighlight(highlightFromUCI(`${moveFrom}${square}${result.promotion??''}`));

            // post to api
            setIsLoading(true);
            handleMove(`${moveFrom}${square}${result.promotion ?? ''}`)
            .catch(() => {
                chessGame.undo(); // if server problem, roll back locally
                setBoardPosition(chessGame.fen());
            })
            .finally(() => setIsLoading(false));

            setOptionSquares({});
            setMoveFrom('');
            return;
        
        } catch {
            // if illegal, setMoveFrom and getMoveOptions to the new clicked square
            const hasMoveOptions = getMoveOptions(square as Square);

            // if new piece, setMoveFrom, otherwise clear moveFrom
            if (hasMoveOptions) {
                setMoveFrom(square);
            }

            // return early
            return;
        }
    }, [chessGame, moveFrom, handleMove]);

    return (
        <div className={styles.container}>
            <div className={styles.chessboardContainer}>
                <div className={styles.countdown}>
                    {isLoading
                        ? `Engine is thinking… ${countdown}s`
                        : `Your turn!`
                    }
                    
                    <img
                        src={cogUrl}
                        alt="Loading spinner"
                        className={`${styles.spinner} ${
                            isLoading ? styles.spinnerVisible : styles.spinnerHidden
                        }`}
                    />
                    </div>
                {/* positions explored and depth reached stats */}
                <div className={styles.engineStats}>
                    <span className={styles.stat}>
                        Depth Reached:&nbsp;
                        <Odometer
                            value={depthSearched}
                            format="(,ddd)"
                            duration={150}
                            theme="default"
                            className={styles.odometerInline}
                        />
                    </span>

                    <span className={styles.stat}>
                        Positions Explored:&nbsp;
                        <Odometer
                            value={positionsSearched}
                            format="(,ddd)"
                            duration={500}
                            theme="default"
                            className={styles.odometerInline}
                        />
                    </span>
                </div>
                <Chessboard 
                    position={boardPosition}
                    onPieceDrop={onDrop}
                    onSquareClick={isLoading ? undefined : onSqrClick} // only makes moves if not loading
                    arePiecesDraggable={!isLoading} // can only drag pieces when not loading
                    customSquareStyles={{
                        ...optionSquares,
                        ...checkHighlight,
                        ...lastMoveHighlight,
                    }}
                    onPieceDragBegin={onDragBegin}
                    onPieceDragEnd={onDragEnd}
                    customDropSquareStyle={{
                        boxShadow: "inset 0 0 1px 4px rgba(255,255,255,0.6)"
                    }}
                    showBoardNotation={false}
                    customBoardStyle={{
                        borderRadius: '10px',
                        boxShadow: '0 0 50px rgba(0, 0, 0, 1)',
                    }}
                />
            </div>
        </div>
    );
}

export default Game;