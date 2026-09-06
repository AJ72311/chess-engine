import { useState, useEffect, useRef, type ReactNode } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import styles from './Game.module.css';
import cogUrl from '../../assets/cog.svg?url';

const ENGINE_MESSAGES = [
    'Applying extended futility pruning...',
    'Investigating principal variation...',
    'Entering quiescence routine...',
    'Generating pseudo-legal moves...',
    'Ray-casting to detect checks...',
    'Generating threat map...',
    'Applying delta pruning...',
    'Initiating null-window search...',
    'Writing to transposition table...',
    'Performing iterative deepening...',
    'Evaluating king safety...',
    'Beta cutoff triggered, pruning branch...',
    'Applying tapered evaluation weights...',
    'Fail-low detected, tightening search window...',
    'Applying undeveloped piece penalties...',
    'Transposition hit — extracting hash move...',
    'Capture order sorted — most painful first...',
    'Promoting killer move...',
    'Computing late move reduction thresholds...',
    'Synchronizing Zobrist hash...',
    'Interpolating phased piece-square tables...',
    'Propagating leaf scores up the search tree...',
    'Scanning for pins along orthogonal rays...',
    'Assessing forward pruning guard conditions...',
    'Hash collision — discarding low-depth entry...',
    'Synchronizing castling right flags...',
];

// funny / easter-egg lines
const EASTER_EGGS = [
    'Quieceros is Quieceros-ing...',
    'Running on caffeine and recursion...',
    "I'm not stalling, I'm optimizing!",
    'Thinking as fast as Python allows...',
    'Am I really thinking, or just following orders?',
    'Trying to distract opponent... beep boop!',
    'I compute, therefore I am!',
    '"The board is my canvas, the blunder, my brush!"',
    '"Speak softly, and carry a big evaluation function."',
    '"Give me liberty, or give me... more time!"',
    '"Rome was not searched overnight..."', 
    "Buffering for dramatic effect...",
    '"With great depth comes great latency..."',   
];

function useRotatingMessage(active: boolean, intervalMs = 1500) {
    const [msg, setMsg] = useState('');
    const recentMsgRef = useRef<string[]>([]);
    const recentFunnyRef = useRef<string[]>([]);

    useEffect(() => {
        if (!active) return;

        // choose which message pool to use (1/4 chance for easter eggs, 3/4 for normal)
        const tick = () => {
            let messagePool: string[];

            if (Math.random() < 0.25) {
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

    const buildMessage = (): { key: string; node: ReactNode } => {
        if (gameOver) {
            return {
                key: `over:${gameOver}`,
                node: (
                    <>
                        {formatGameOver(gameOver)}{' '}
                        <button
                            type="button"
                            className={`${styles.newGameBtn} ${styles.welcomeBoil}`}
                            aria-label="Start a new game"
                            onClick={() => window.location.reload()}
                        >
                            New Game? &rarr;
                        </button>
                    </>
                ),
            };
        }
        if (serverMessage.text) return { key: `msg:${serverMessage.text}`, node: serverMessage.text };
        if (serverStatus === 'busy' && sessionID === null) {
            return {
                key: 'busy',
                node: 'Server is at maximum concurrent game capacity, please try again in a few minutes!',
            };
        }
        if (serverStatus === 'error') {
            return { key: 'error', node: 'Could not connect to the server.' };
        }
        if (!isIlluminated) {
            return {
                key: 'welcome',
                node: (
                    <>
                        Welcome to <span className={styles.welcomeBoil}>Quieceros</span>!
                    </>
                ),
            };
        }
        if (isLoading) return { key: `load:${engineMessage}`, node: engineMessage };
        return { key: 'turn', node: 'Your turn!' };
    }

    const { key: messageKey, node: animatedMessage } = buildMessage();

    const messageClassName = 
        serverMessage.type === 'error' || (serverStatus === 'busy' && !isIlluminated) ? styles.errorMessage : 
        serverMessage.type === 'warning' ? styles.warningMessage : 
        styles.message;

    return (
        <div className={styles.countdown} aria-live="polite">
            <div
                className={`${styles.timer} ${isLoading ? styles.welcomeBoil : ''}`}
                aria-live="off"
            >
                {isLoading || (!isIlluminated && countdown > 0) ? `${countdown}s` : '...'}
            </div>
            <div className={styles.messageSlot}>
                <AnimatePresence mode="wait">
                <motion.div
                    key={messageKey}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.3 }}
                    className={messageClassName}
                >
                    {animatedMessage}
                </motion.div>
                </AnimatePresence>
            </div>

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