import { useState, useRef, useCallback, type CSSProperties, useEffect } from 'react';
import { Chessboard } from 'react-chessboard';
import { Chess, type Square } from 'chess.js';
import styles from './Game.module.css';

type SquareStyles = Partial<Record<Square, CSSProperties>>;

function Game() {
    // create a chess.js instance using ref to maintain game state across renders
    const chessGameRef = useRef(new Chess());
    const chessGame = chessGameRef.current;

    // track current position FEN in state to trigger re-renders
    const [boardPosition, setBoardPosition] = useState<string>(chessGame.fen());
    
    // used for showing move options when clicking on a piece
    const [moveFrom, setMoveFrom] = useState<string>('');
    const [optionSquares, setOptionSquares] = useState<object>({});

    // used for highlighting king's square when in check
    const [checkHighlight, setCheckHighlight] = useState<object>({});

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

    // runs upon a new move
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
            background: 'rgba(255, 255, 0, 0.4)',
        };

        setOptionSquares(newSquares);
        return true;
    }

    const onDragBegin = useCallback((_piece: string, source: Square) => {
        // get all legal moves from this square
        const moves = chessGame.moves({ square: source, verbose: true });
        
        // build a styles object for each target square and the source square
        const styles: SquareStyles = {};
        // highlight the departing square in yellow
        styles[source] = { background: 'rgba(255,255,0,0.4)' };

        // show dots on target squares
        moves.forEach(move => {
            styles[move.to] = {
                background: chessGame.get(move.to) &&
                chessGame.get(move.to)?.color !== 
                chessGame.get(source)?.color ? 
                'radial-gradient(circle, rgba(0,0,0,.1) 85%, transparent 85%)' : // big circle if capture
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
            chessGame.move({
                from: sourceSqr,
                to: destinationSqr,
                promotion: 'q', // always promote to queen for simplicity
            });

            // if the move succeeded
            setBoardPosition(chessGame.fen());
            return true;
        
        } catch {
            // if the move failed
            return false;
        }
    }, [chessGame]);

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
            chessGame.move({
                from: moveFrom,
                to: square,
                promotion: 'q', // always promote to queen for simplicity
            });

            // if move succeeded, clear and return
            setBoardPosition(chessGame.fen());
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
    }, [chessGame, moveFrom]);

    return (
        <div className={styles.container}>
            <div className={styles.chessboardContainer}>
                <Chessboard 
                    position={boardPosition}
                    onPieceDrop={onDrop}
                    onSquareClick={onSqrClick}
                    customSquareStyles={{
                        ...optionSquares,
                        ...checkHighlight,
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