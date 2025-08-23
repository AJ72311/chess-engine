import Game from './components/Game/Game';
import GithubLogo from './assets/github.svg';
import styles from './App.module.css';
import { useState, useEffect } from 'react';

function App() {
    const [isIlluminated, setIsIlluminated] = useState<boolean>(false);
    const [startupCountdown, setStartupCountdown] = useState<number>(5);

    // The illumination timer logic now lives in the parent
    useEffect(() => {
        if (isIlluminated) return;

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
    }, [isIlluminated]);

    return (
        <div className={styles.appContainer}>
            <a
                href="https://github.com/AJ72311/chess-engine"
                target="_blank"
                rel="noopener noreferrer"
                className={`${styles.githubLink} ${isIlluminated ? styles.illuminated : ''}`}
            >
                <img src={GithubLogo} alt="GitHub Logo" className={styles.githubLogo} />
            </a>
            <Game 
                isIlluminated={isIlluminated}
                startupCountdown={startupCountdown}
            />
        </div>
    );
}

export default App;