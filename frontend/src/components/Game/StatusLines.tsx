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
    'Generating legal moves...',
    'Applying delta pruning...',
    'Probing transposition table...',
    'Position already analyzed - skipping...',
    'Writing to transposition table...',
    'Performing iterative deepening...',
    'Evaluating king safety...',
    'Assessing material imbalance...',
    'Consulting piece-square tables...',
    'Tightening alpha-beta bounds...',
    'Beta cutoff triggered...',
    'Applying tapered evaluation weights...',
    'Finalizing evaluation...',
    'Engine thinks this position is cursed...',
    'Running on caffeine and recursion...',
    'Warning: humans may not understand this move...',
    'The silicon brain is thinking hard...',
    'Accessing ancient chess wisdom...',
    "If I had emotions, I'd be stressed right now...",
    'Calculating the meaning of life... and this move...',
    "I'm not stalling, I'm optimizing!",
    'Please wait... overthinking in progress...',
    'Thinking as fast as Python allows...',
    'Mentally moving a knight in circles...',
    "Yes, this is the best move. Trust me, I'm an engine...",
    "A lesser engine would hesitate...",
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

    const engineMessage = useRotatingMessage(isLoading, 1800);
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