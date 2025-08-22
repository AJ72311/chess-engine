import { useState, useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import styles from './Game.module.css';
import cogUrl from '../../assets/cog.svg?url'

const ENGINE_MESSAGES = [
    'Applying futility pruning',
    'Investigating principle variation...',
    'Applying late move reductions...',
    'Entering quiescence routine...',
    'Evaluating killer move candidates...',
    'Move-ordering in progress...',
    'Updating history table...',
    'Generating pseudo-legal moves...',
    'Filtering illegal moves...',
    'Detecting checks and pins...',
    'Ray-casting to detect attacks...',
    'Generating threat map...',
    'Applying delta pruning...',
    'Probing transposition table...',
    'Writing to transposition table...',
    'Performing iterative deepening...',
    'Evaluating king safety...',
    'Assessing material imbalance...',
    'Consulting piece-square tables...',
    'Tightening alpha-beta bounds...',
    'Beta cutoff triggered, pruning branch...',
    'Applying tapered evaluation weights...',
    'Finalizing evaluation...',
    'De-prioritizing unpromising lines...',
    'Fail-low detected, widening search window...',
    'Gauging piece development...',
    'Prioritizing principal variation line...',
    'Hash match found - reusing stored evaluation...',
    'Replacing old TT entry...',
    'Applying undeveloped piece penalties...',
    'Stand-pat test passed, terminating quiescence...',
    'Null-window search failed-high, initiating re-search...',
    'Transposition hit - hash move retrieved...',
    'Ordering candidate moves...',
    'Prioritizing promising exchanges...',
    'Sorting captures with MVV-LVA...',
    'Capture order sorted - most painful first...',
    'Promoting killer move...',
    'Applying history heuristic...',
    'Identifying potential pawn breaks...',
    'Scoring quiet moves...',
    'Applying central control bonuses...',
    'Analyizing exchange sacrifices...',
    
    // funny / easter-egg lines 
    'Wishing I was a Go engine right now...',
    'Running on caffeine and recursion...',
    'Bribing the king to spill secrets...',
    'Accessing ancient chess wisdom...',
    'Training pawns to think outside the box...',
    "I'm not stalling, I'm optimizing!",
    'Thinking as fast as Python allows...',
    'Considering early retirement...',
    'Trying to distract opponent... beep boop!',
    'Auditing knight hops for tax purposes...',
    "Assessing opponent's aura...",
    'Consulting magic 8-ball for move approval...',
];

function useRotatingMessage(active: boolean, intervalMs = 1500) {
    const [msg, setMsg] = useState(() => {
        // pick one random message to start
        return ENGINE_MESSAGES[
            Math.floor(Math.random() * ENGINE_MESSAGES.length)
        ];
    });

    useEffect(() => {
        if (!active) return;

        const tick = () => {
            const next =
                ENGINE_MESSAGES[
                    Math.floor(Math.random() * ENGINE_MESSAGES.length)
                ];

            setMsg(next);
        }

        // immediately set a message, then rotate
        tick();
        const id = setInterval(tick, intervalMs);
        return () => clearInterval(id);
    }, [active, intervalMs]);

    return msg;
}

export function StatusLines({
    gameOver,
    isLoading,
    countdown,
} : {
    gameOver: string
    isLoading: boolean
    countdown: number
}) {
     // helper to format game over text
    const formatGameOver = (s: string) =>
        `${s.charAt(0).toUpperCase()}${s.slice(1)}!`

    const engineMessage = useRotatingMessage(isLoading, 2000);
    const animatedMessage = gameOver
    ? formatGameOver(gameOver)
    : isLoading
    ? `${engineMessage}`
    : 'Your turn!'

    return (
        <div className={styles.countdown} aria-live="polite">
            <div className={styles.timer} aria-live="off">
                {isLoading
                    ? `${countdown}s`          
                    : '...' 
                }
            </div>
            <AnimatePresence mode="wait">
            <motion.div
                key={animatedMessage}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.3 }}
                className={styles.message}
            >
                {animatedMessage}
            </motion.div>
            </AnimatePresence>

            <img
            src={cogUrl}
            alt="Loading spinner"
            className={`
                ${styles.spinner}
                ${isLoading && !gameOver
                ? styles.spinnerVisible
                : styles.spinnerHidden}
            `}
            />
        </div>
    );
}