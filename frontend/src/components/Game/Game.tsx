import { useState, useRef, useCallback, type CSSProperties, useEffect } from 'react';
import { Chessboard } from 'react-chessboard';
import { Chess, type Square } from 'chess.js';
import { StatusLines } from './StatusLines'
import styles from './Game.module.css';
import axios from 'axios';
import Odometer from 'react-odometerjs';
import 'odometer/themes/odometer-theme-default.css';

type SquareStyles = Partial<Record<Square, CSSProperties>>;

function Game({
    isIlluminated,
    startupCountdown,
    initialServerStatus,
    isStartingUp,
} : {
    isIlluminated: boolean
    startupCountdown: number
    initialServerStatus: string
    isStartingUp: boolean
}) {
    // create a chess.js instance using ref to maintain game state across renders
    const chessGameRef = useRef(new Chess());
    const chessGame = chessGameRef.current;

    // track current position FEN in state to trigger re-renders
    const [boardPosition, setBoardPosition] = useState<string>(chessGame.fen());
    const [gameOver, setGameOver] = useState<string>('');
    
    // used for showing move options and highlights when clicking on a piece
    const [moveFrom, setMoveFrom] = useState<string>('');
    const [optionSquares, setOptionSquares] = useState<object>({});
    const [checkHighlight, setCheckHighlight] = useState<object>({});
    const [lastMoveHighlight, setLastMoveHighlight] = useState<object>({});

    // used to track the session with the engine's api
    const [sessionID, setSessionID] = useState<string | null>(null);
    const [isSessionExpired, setIsSessionExpired] = useState<boolean>(false);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [countdown, setCountdown] = useState<number>(0);
    const [positionsSearched, setPositionsSearched] = useState<number>(0);
    const [depthSearched, setDepthSearched] = useState<number>(0);
    const [isBookMove, setIsBookMove] = useState<boolean>(false);

    // used to animate odometer when going from a book move to a normal one
    const [odometerPositions, setOdometerPositions] = useState<number>(0);
    const [odometerDepth, setOdometerDepth] = useState<number>(0);  
    
    // used to track server status and messages
    const [serverStatus, setServerStatus] = useState<string>(initialServerStatus);
    const [serverMessage, setServerMessage] = useState<{ type: string, text: string }>({ type: 'info', text: '' });

    // update the local serverStatus when its prop changes
    useEffect(() => {
        setServerStatus(initialServerStatus);
    }, [initialServerStatus]);

    // refs to hold Ids for setTimeout calls for session expiration
    const timeoutWarningRef = useRef<number | null>(null);
    const timeoutExpirationRef = useRef<number | null>(null);

    // resets session timeout timers, called after each player move
    const resetTimeoutTimer = useCallback(() => {
        // clear existing timers
        if (timeoutWarningRef.current) clearTimeout(timeoutWarningRef.current);
        if (timeoutExpirationRef.current) clearTimeout(timeoutExpirationRef.current);

        // clear lingering timeout messages
        setServerMessage({ type: 'info', text: '' });
        setIsSessionExpired(false);

        // set a new warning timer for 10 minutes (600,000 milliseconds)
        timeoutWarningRef.current = setTimeout(() => {
            setServerMessage({ 
                type: 'warning',
                text: 'Session will expire in 5 minutes due to inactivity, play a move!',
            });
        }, 600 * 1000);

        // set a new expiration timer for 15 minutes (900,000 milliseconds)
        timeoutExpirationRef.current = setTimeout(() => {
            setServerMessage({
                type: 'error',
                text: 'Session has expired, reload to start a new game!',
            });

            // invalidate sessionID on the client side
            setSessionID(null);
            setIsSessionExpired(true);
        }, 900 * 1000);
    }, []);

    // cleanup timers on component unmount
    useEffect(() => {
        return () => {
            if (timeoutWarningRef.current) clearTimeout(timeoutWarningRef.current);
            if (timeoutExpirationRef.current) clearTimeout(timeoutExpirationRef.current);
        };
    }, []); 

    // briefly set odometer values to 0 to ensure animation when transitioning from "Book Move" string
    const wasBookMoveRef = useRef<boolean>(false);
    useEffect(() => {
        if (wasBookMoveRef.current && !isBookMove) {
            setOdometerDepth(0);
            setOdometerPositions(0);

            const timer = setTimeout(() => {
                setOdometerPositions(positionsSearched);
                setOdometerDepth(depthSearched);
            }, 20);


            return () => clearTimeout(timer);
        
        } else if (!isBookMove) {
            setOdometerDepth(depthSearched);
            setOdometerPositions(positionsSearched);
        }
    }, [isBookMove, depthSearched, positionsSearched]);

    // keep wasBookMoveRef updated
    useEffect(() => {
        wasBookMoveRef.current = isBookMove;
    }, [isBookMove]);

    // try a player's move, get the engine's response if player move is valid
    const handleMove = useCallback(async (playerMove: string) => {
        // get the engine's reply
        setIsLoading(true);
        try {
            const endpoint = sessionID ? '/game/play-move' : '/game/new-game';
            const payload = sessionID
            ? {
                'session_id': sessionID,
                'player_move': playerMove,
                'client_fen': boardPosition,
            } : {
                'player_move': playerMove,
            }

            const data = await axios.post(endpoint, payload);

            // unpack response
            const newFEN = data.data.new_fen;
            const movePlayed = data.data.move_played;
            const depthReached = data.data.depth_reached;
            const nodesSearched = data.data.nodes_searched;
            const gameID = data.data.game_id ? data.data.game_id : null; // gameID only in /new-game
            setIsBookMove(data.data.is_book);

            if (data.data.server_status) {
                setServerStatus(data.data.server_status)
            }

            const result = chessGame.move(movePlayed);
            // safety check: if move was illegal, log  error and load the returned FEN
            if (result === null) {
                console.error(
                    "Engine returned an illegal move:",
                    movePlayed, 
                    "Falling back to FEN load."
                );
                chessGame.load(newFEN);
            }

            setBoardPosition(newFEN);
            setPositionsSearched(nodesSearched);
            setDepthSearched(depthReached);
            setLastMoveHighlight(highlightFromUCI(movePlayed));

            if (gameID) {
                setSessionID(gameID);
            }

            // check for game over after the engine's move
            if (chessGame.isGameOver()) {
                const reason = chessGame.isCheckmate() 
                ? 'checkmate' 
                : chessGame.isStalemate()
                ? 'stalemate'
                : 'draw';

                setGameOver(reason);
                return; 
            }
        
        } catch (error: any) {
            if (error.response && error.response.status === 503) {
                setServerMessage({
                    type: 'error',
                    text: 'Server is at maximum concurrent game capacity, please check again in a few minutes.'
                });
                setServerStatus('busy');
            }

            if (error.response && error.response.status === 404) {
                setServerMessage({
                    type: 'error',
                    text: 'Session has expired, reload to start a new game!',
                });
                setSessionID(null);
            }

            throw error;  // re-throw for onDrop / onSquareClick to catch
        
        } finally {
            setIsLoading(false)
        }
    }, [sessionID, boardPosition, chessGame]);

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

            // reset session timeout timers
            resetTimeoutTimer();

            // if the move succeeded
            setBoardPosition(chessGame.fen());
            setLastMoveHighlight(highlightFromUCI(`${sourceSqr}${destinationSqr}${result.promotion??''}`));

            // check for game over after the player's move
            if (chessGame.isGameOver()) {
                const reason = chessGame.isCheckmate() 
                ? 'checkmate' 
                : chessGame.isStalemate()
                ? 'stalemate'
                : 'draw';

                setGameOver(reason);
                return true; // don't get engine's response if game is over
            }

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
    }, [chessGame, handleMove, resetTimeoutTimer]);

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

            // reset session timeout timers
            resetTimeoutTimer();

            // if move succeeded
            setBoardPosition(chessGame.fen());
            setLastMoveHighlight(highlightFromUCI(`${moveFrom}${square}${result.promotion??''}`));

            // check for game over after the player's move
            if (chessGame.isGameOver()) {
                const reason = chessGame.isCheckmate() 
                ? 'checkmate' 
                : chessGame.isStalemate()
                ? 'stalemate'
                : 'draw';

                setGameOver(reason);
                return; // don't get engine's response if game is over
            }

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
    }, [chessGame, moveFrom, handleMove, resetTimeoutTimer]);

    return (
        <div className={styles.container}>
            {/* {(serverStatus === 'heavy_load' || serverStatus === 'busy') && !gameOver && isIlluminated && (
                <div className={styles.heavyLoadIndicator}>
                    Server is under heavy load. Move quality may be reduced.
                </div>
            )} */}
            <div className={styles.chessboardContainer}>
                <div className={`${styles.statusWrapper} ${isIlluminated ? styles.illuminated : ''}`}>
                    <StatusLines 
                        gameOver={gameOver}
                        isLoading={isLoading}
                        isIlluminated={isIlluminated}
                        countdown={startupCountdown > 0 ? startupCountdown : countdown}
                        serverStatus={serverStatus}
                        serverMessage={serverMessage}
                        sessionID={sessionID}
                        isStartingUp={isStartingUp}
                    />
                </div>
                <div className={`${styles.engineInfo} ${isIlluminated ? styles.illuminated : ''}`}>
                    {/* positions explored and depth reached stats */}
                    <div className={styles.engineStats}>
                        <span className={styles.stat}>
                            Depth Reached:&nbsp;
                            {
                                chessGame.history().length < 2 ? '...' : isBookMove ? (
                                    'Book Move'
                                ) : (
                                    <Odometer
                                        value={odometerDepth}
                                        format="(,ddd)"
                                        duration={150}
                                        className={styles.odometerInline}
                                    />
                                )
                            }
                        </span>

                        <span className={styles.stat}>
                            Positions Explored:&nbsp;
                            {
                                chessGame.history().length < 2 ? '...' : isBookMove ? (
                                    'Book Move'
                                ) : (
                                    <Odometer
                                        value={odometerPositions}
                                        format="(,ddd)"
                                        duration={150}
                                        className={styles.odometerInline}
                                    />
                                )
                            }
                        </span>
                    </div>
                </div>
                <div className={`${styles.chessboardWrapper} ${isIlluminated ? styles.illuminated : ''}`}>
                    <Chessboard 
                        position={boardPosition}
                        onPieceDrop={onDrop}
                        onSquareClick={
                            (
                                isLoading || !isIlluminated || gameOver || isSessionExpired 
                                || (sessionID === null && serverStatus === 'busy')
                            ) 
                            ? undefined 
                            : onSqrClick
                        }
                        arePiecesDraggable={
                            !isLoading && isIlluminated && !gameOver && !isSessionExpired
                            && (sessionID !== null || serverStatus !== 'busy')
                        }
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
                            transition: 'box-shadow 1.5s ease-in-out',
                        }}
                    />
                </div>
                <div 
                    className={`
                        ${styles.statusIndicator} 
                        ${(isLoading || !isIlluminated || gameOver || isSessionExpired) ? styles.statusBusy : ''}
                    `}
                ></div>
            </div>
        </div>
    );
}

export default Game;