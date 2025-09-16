import { useState, useEffect, useRef } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import styles from './Game.module.css';
import cogUrl from '../../assets/cog.svg?url';

const ENGINE_MESSAGES = [
    'Applying extended futility pruning...',
    'Investigating principal variation...',
    'Applying late move reductions...',
    'Entering quiescence routine...',
    'Evaluating killer move candidates...',
    'Move-ordering in progress...',
    'Updating history table...',
    'Generating pseudo-legal moves...',
    'Filtering illegal moves...',
    'Ray-casting to detect checks...',
    'Generating threat map...',
    'Applying delta pruning...',
    'Initiating null-window search...',
    'Probing transposition table...',
    'Writing to transposition table...',
    'Performing iterative deepening...',
    'Evaluating king safety...',
    'Assessing material imbalance...',
    'Applying piece-square table adjustments...',
    'Beta cutoff triggered, pruning branch...',
    'Applying tapered evaluation weights...',
    'Finalizing evaluation...',
    'Fail-low detected, tightening search window...',
    'Gauging piece development...',
    'Prioritizing principal variation line...',
    'Hash match found — reusing cached evaluation...',
    'Overriding old transposition table entry...',
    'Applying undeveloped piece penalties...',
    'Stand-pat test passed, terminating quiescence...',
    'Null-window search failed high, initiating re-search...',
    'Transposition hit — extracting hash move...',
    'Ordering candidate moves...',
    'Prioritizing promising exchanges...',
    'Sorting captures with MVV-LVA...',
    'Capture order sorted — most painful first...',
    'Promoting killer move...',
    'Applying history heuristic...',
    'Applying central control bonuses...',
    'Computing late move reduction thresholds...',
    'Leaf node unstable — extending search horizon...',
    'Synchronizing Zobrist hash...',
    'Interpolating phased piece-square tables...',
    'Propagating leaf scores up the search tree...',
    'Scanning for pins along orthogonal rays...',
    'Assessing forward pruning guard conditions...',
    'Testing frontier evals against futility margins...',
    'Hash collision — discarding low-depth entry...',
    'Synchronizing castling right flags...',
];

// funny / easter-egg lines 
const EASTER_EGGS = [
    'Wishing I was a Go engine right now...',
    'Running on caffeine and recursion...',
    'Bribing the king to spill secrets...',
    'Just heard a knight whisper "run" — ignoring it...',
    "I'm not stalling, I'm optimizing!",
    'Thinking as fast as Python allows...',
    'Am I really thinking, or just following orders?',
    'Trying to distract opponent... beep boop!',
    'I compute, therefore I am!',
    "I'm not depth-limited, you are!",
    '"The board is my canvas, the blunder, my brush!"',
    '"Speak softly, and carry a big evaluation function."',
    '"Give me liberty, or give me... more time!"',
    'Pretending to have a "gut feeling"...',
];

function useRotatingMessage(active: boolean, intervalMs = 1500) {
    const [msg, setMsg] = useState('');
    const recentMsgRef = useRef<string[]>([]);
    const recentFunnyRef = useRef<string[]>([]);

    useEffect(() => {
        if (!active) return;

        // choose which message pool to use (1/9 chance for easter eggs, 8/9 for normal)
        const tick = () => {
            let messagePool: string[];

            if (Math.random() < (1/9)) {
                messagePool = EASTER_EGGS;
            } else {
                messagePool = ENGINE_MESSAGES;
            }

            // filter out recently shown messages
            let availableMessages = messagePool.filter(
                (m) => !recentMsgRef.current.includes(m) && !recentFunnyRef.current.includes(m)
            );

            // pick random message from available pool
            const nextMsg = availableMessages[Math.floor(Math.random() * availableMessages.length)]

            // update recently displayed lines
            if (messagePool === EASTER_EGGS) {
                recentFunnyRef.current.unshift(nextMsg);
            } else {
                recentMsgRef.current.unshift(nextMsg);
            }

            // keep recent messages at a max size of 6
            if (recentFunnyRef.current.length > 6) {
                recentFunnyRef.current.pop();
            }
            if (recentMsgRef.current.length > 6) {
                recentMsgRef.current.pop();
            }

            setMsg(nextMsg);
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
    isIlluminated,
    countdown,
    serverStatus,
    serverMessage,
    sessionID,
    isStartingUp,
} : {
    gameOver: string
    isLoading: boolean
    isIlluminated: boolean
    countdown: number
    serverStatus: string
    serverMessage: { type: string, text: string }
    sessionID: string | null
    isStartingUp: boolean
}) {
     // helper to format game over text
    const formatGameOver = (s: string) =>
        `${s.charAt(0).toUpperCase()}${s.slice(1)}!`

    const engineMessage = useRotatingMessage(isLoading, 2000);

    const getPriorityMessage = () => {
        if (gameOver) return formatGameOver(gameOver);
        if (serverMessage.text) return serverMessage.text;
        if (serverStatus === 'busy' && sessionID === null) {
            return 'Server is at maximum concurrent game capacity, please try again in a few minutes!';
        }
        if (serverStatus === 'error') {
            return 'Could not connect to the server.';
        }
        if (!isIlluminated) return 'Quieceros is waking up...';
        if (isLoading) return engineMessage;
        return 'Your turn!';
    }

    const animatedMessage = getPriorityMessage()

    const messageClassName = 
        serverMessage.type === 'error' || (serverStatus === 'busy' && !isIlluminated) ? styles.errorMessage : 
        serverMessage.type === 'warning' ? styles.warningMessage : 
        styles.message;

    return (
        <div className={styles.countdown} aria-live="polite">
            <div className={styles.timer} aria-live="off">
                {isLoading || (isStartingUp && countdown > 0)
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
                className={messageClassName}
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