import Game from './components/Game/Game';
import GithubLogo from './assets/github.svg';
import EngineLogo from './assets/icon.svg';
import PythonLogo from './assets/python.svg';
import styles from './App.module.css';
import { useState, useEffect } from 'react';
import apiClient from './api.ts';

const ENGINE_BLURB =
    'Quieceros is named after quiescence search, a selective extension to alpha-beta search that mitigates tactical errors at volatile leaf nodes. Building the quiescence routine was my favorite part of developing Quieceros!';

const GITHUB_URL = 'https://github.com/AJ72311/chess-engine';

// on touch / narrow layouts the icons open a tap popover instead of the desktop hover tooltip
const isCompactLayout = () =>
    typeof window !== 'undefined' && window.matchMedia('(max-width: 600px)').matches;

function App() {
    const [isIlluminated, setIsIlluminated] = useState<boolean>(false);
    const [startupCountdown, setStartupCountdown] = useState<number>(3);
    const [serverStatus, setServerStatus] = useState<string>('checking');
    const [isStartingUp, setIsStartingUp] = useState<boolean>(false);
    const [showEngineInfo, setShowEngineInfo] = useState<boolean>(false);
    const [showGithubInfo, setShowGithubInfo] = useState<boolean>(false);

    // runs on component mount to check server capacity
    useEffect(() => {
        const checkServerStatus = async () => {
            try {
                const { data } = await apiClient.get('/game/status');
                setServerStatus(data.status);

                // if the status is good, start the startup sequence.
                if (data.status === 'ok' || data.status === 'heavy_load') {
                    setIsStartingUp(true);
                }

            } catch (err) {
                console.error('Failed to check server status: ', err);
                setServerStatus('error');
            }
        };
        checkServerStatus();
    }, []);

    // count down the dimmed "welcome" state, then play the illumination reveal at zero
    useEffect(() => {
        if (isIlluminated || !isStartingUp) {
            return;
        }

        const interval = setInterval(() => {
            setStartupCountdown(prev => {
                if (prev <= 1) {
                    clearInterval(interval);
                    setIsIlluminated(true);
                    document.body.classList.add('illuminated');
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);

        return () => clearInterval(interval);
    }, [isIlluminated, isStartingUp]);

    return (
            <div className={styles.appContainer}>
                <header className={styles.header}>
                    <div className={styles.iconsContainer}>
                        <div className={styles.engineIconSlot}>
                            <button
                                type="button"
                                className={`
                                    ${styles.iconLink} ${styles.engineIconLink}
                                    ${isIlluminated ? styles.illuminated : ''}
                                `}
                                data-tooltip={ENGINE_BLURB}
                                aria-label="About the name Quieceros"
                                aria-expanded={showEngineInfo}
                                onClick={() => {
                                    setShowEngineInfo(open => !open);
                                    setShowGithubInfo(false);
                                }}
                            >
                                <img src={EngineLogo} alt="Engine Logo" className={styles.icon} />
                            </button>
                            {showEngineInfo && (
                                <>
                                    <div
                                        className={styles.popoverBackdrop}
                                        onClick={() => setShowEngineInfo(false)}
                                    />
                                    <div
                                        className={styles.iconPopover}
                                        role="dialog"
                                        aria-label="About the name Quieceros"
                                    >
                                        <button
                                            type="button"
                                            className={styles.popoverClose}
                                            aria-label="Close"
                                            onClick={() => setShowEngineInfo(false)}
                                        >
                                            &times;
                                        </button>
                                        <p className={styles.popoverText}>{ENGINE_BLURB}</p>
                                    </div>
                                </>
                            )}
                        </div>
                        <div className={styles.githubIconSlot}>
                            <a
                                href={GITHUB_URL}
                                target="_blank"
                                rel="noopener noreferrer"
                                className={`
                                    ${styles.iconLink} ${styles.githubIconLink}
                                    ${isIlluminated ? styles.illuminated : ''}
                                `}
                                data-tooltip="Check out the repo!"
                                aria-expanded={showGithubInfo}
                                onClick={(e) => {
                                    if (isCompactLayout()) {
                                        e.preventDefault();
                                        setShowGithubInfo(open => !open);
                                        setShowEngineInfo(false);
                                    }
                                }}
                            >
                                <img src={GithubLogo} alt="GitHub Logo" className={styles.icon} />
                            </a>
                            {showGithubInfo && (
                                <>
                                    <div
                                        className={styles.popoverBackdrop}
                                        onClick={() => setShowGithubInfo(false)}
                                    />
                                    <div
                                        className={styles.iconPopover}
                                        role="dialog"
                                        aria-label="Open the GitHub repository"
                                    >
                                        <button
                                            type="button"
                                            className={styles.popoverClose}
                                            aria-label="Close"
                                            onClick={() => setShowGithubInfo(false)}
                                        >
                                            &times;
                                        </button>
                                        <p className={styles.popoverText}>
                                            Want to see how Quieceros works under the hood?
                                        </p>
                                        <a
                                            href={GITHUB_URL}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className={styles.popoverAction}
                                            onClick={() => setShowGithubInfo(false)}
                                        >
                                            Check out the repo! &rarr;
                                        </a>
                                    </div>
                                </>
                            )}
                        </div>
                    </div>
                </header>
                <Game
                    isIlluminated={isIlluminated}
                    startupCountdown={serverStatus === 'checking' ? 0 : startupCountdown}
                    initialServerStatus={serverStatus}
                    isStartingUp={isStartingUp}
                />
                <div className={`${styles.topLeftText} ${isIlluminated ? styles.illuminated : ''}`}>
                    <span className={
                        `${styles.engineName} ${isIlluminated ? styles.illuminated : ''}`
                    }>
                        Quieceros
                    </span>
                    <span> &mdash; </span>
                    <img
                        src={PythonLogo}
                        alt="Python Logo"
                        className={styles.inlineLogo}
                    />
                    <span className={`${styles.authorNameBlock} ${isIlluminated ? styles.illuminated : ''}`}>
                        <span> Chess Engine by </span>
                        <i>AJ Yaseen</i>
                    </span>
                </div>
        </div>
    );
}

export default App;
