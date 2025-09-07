import Game from './components/Game/Game';
import GithubLogo from './assets/github.svg';
import EngineLogo from './assets/icon.svg';
import styles from './App.module.css';
import { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
    const [isIlluminated, setIsIlluminated] = useState<boolean>(false);
    const [startupCountdown, setStartupCountdown] = useState<number>(5);
    const [serverStatus, setServerStatus] = useState<string>('checking');
    const [isStartingUp, setIsStartingUp] = useState<boolean>(false);

    useEffect(() => {
        const checkServerStatus = async () => {
            try {
                const { data } = await axios.get('/game/status');
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

    // runs on component mount to check server capacity
    useEffect(() => {
        const checkServerStatus = async () => {
            try {
                const { data } = await axios.get('/game/status');
                setServerStatus(data.status);  // 'ok', 'heavy_load', or 'busy'

            } catch (err) {
                console.error('Failed to check server status: ', err);
                setServerStatus('error');
            }
        };

        checkServerStatus();
    }, []);

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
            <div className={styles.iconsContainer}>
                <a
                    href="#"
                    className={`
                        ${styles.iconLink} ${styles.engineIconLink} 
                        ${isIlluminated ? styles.illuminated : ''}
                    `}
                    data-tooltip={
                        'The name "Quieceros" was inspired by quiescence search: a selective extension to an alpha-beta search for tactical positions. Implementing quiescence search was my favorite part of developing this engine!'
                    }
                >
                    <img src={EngineLogo} alt="Engine Logo" className={styles.icon} />
                </a>
                <a
                    href="https://github.com/AJ72311/chess-engine"
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`
                        ${styles.iconLink} ${styles.githubIconLink} 
                        ${isIlluminated ? styles.illuminated : ''}
                    `}
                    data-tooltip="Check out the repo!"
                >
                    <img src={GithubLogo} alt="GitHub Logo" className={styles.icon} />
                </a>
            </div>
            <Game 
                isIlluminated={isIlluminated}
                startupCountdown={serverStatus === 'checking' ? 0 : startupCountdown}
                initialServerStatus={serverStatus}
                isStartingUp={isStartingUp}
            />
        </div>
    );
}

export default App;