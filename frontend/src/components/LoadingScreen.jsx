import { useEffect, useState } from "react";

export default function LoadingScreen({ onComplete }) {
  const [fadingOut, setFadingOut] = useState(false);
  const [currentMessage, setCurrentMessage] = useState("");
  const [messageVisible, setMessageVisible] = useState(false);

  useEffect(() => {
    const mainTimers = [];
    const statusTimers = [];

    // Slowed down sequence for better readability
    // Total sequence now ~7 seconds
    mainTimers.push(setTimeout(() => setFadingOut(true), 6800));
    mainTimers.push(setTimeout(() => onComplete(), 7400));

    // Status message sequence - 1 second intervals for readability
    const messages = [
      { text: "INITIALIZING ENVIRONMENTAL SENSORS", time: 1800 },
      { text: "LOADING QDRANT KNOWLEDGE BASE", time: 2800 },
      { text: "CONNECTING TO NASA POWER API", time: 3800 },
      { text: "CALIBRATING POLLUTION MODELS", time: 4800 },
      { text: "SYSTEM READY", time: 5800 },
    ];

    messages.forEach((msg) => {
      // Start fade out 300ms before next message or at end of turn
      statusTimers.push(setTimeout(() => {
        setMessageVisible(false);
      }, msg.time - 300));

      // Show new message at target time
      statusTimers.push(setTimeout(() => {
        setCurrentMessage(msg.text);
        setMessageVisible(true);
      }, msg.time));
    });

    return () => {
      mainTimers.forEach(clearTimeout);
      statusTimers.forEach(clearTimeout);
    };
  }, [onComplete]);

  return (
    <div className={`ls-viewport ${fadingOut ? "ls-fade-out" : ""}`}>
      <style>{`
        .ls-viewport {
          position: fixed;
          top: 0;
          left: 0;
          width: 100vw;
          height: 100vh;
          background: #000810;
          overflow: hidden;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          z-index: 9999;
          animation: bgShift 8s infinite alternate;
          transition: opacity 0.6s ease-in-out;
        }
        .ls-fade-out { opacity: 0; pointer-events: none; }

        @keyframes bgShift {
          0% { background-color: #000810; }
          50% { background-color: #001a0e; }
          100% { background-color: #000d1a; }
        }

        .ls-overlay {
          position: absolute;
          inset: 0;
          background: radial-gradient(ellipse 80% 60% at 50% 50%, rgba(0,229,255,0.04) 0%, transparent 70%);
          pointer-events: none;
        }

        .ls-particles {
          position: absolute;
          inset: 0;
          width: 100%;
          height: 100%;
          pointer-events: none;
        }
        .particle { fill: #00e5ff; animation: pulse 4s infinite ease-in-out; }
        @keyframes pulse {
          0%, 100% { opacity: 0.15; }
          50% { opacity: 0.4; }
        }

        .ls-logo-wrapper {
          position: relative;
          width: 200px;
          height: 200px;
          display: flex;
          align-items: center;
          justify-content: center;
          animation: slowRotateContainer 20s linear infinite;
        }
        @keyframes slowRotateContainer { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

        .ls-logo {
          width: 140px;
          height: auto;
          filter: drop-shadow(0 0 20px rgba(0,229,255,0.6)) drop-shadow(0 0 60px rgba(0,229,255,0.2));
          animation: logoReveal 1.2s ease-out forwards, counterRotate 20s linear infinite;
        }
        @keyframes logoReveal { from { opacity: 0; transform: scale(0.3); } to { opacity: 1; transform: scale(1); } }
        @keyframes counterRotate { from { transform: rotate(0deg); } to { transform: rotate(-360deg); } }

        .bracket {
          position: absolute;
          width: 20px;
          height: 20px;
          border: 1.5px solid rgba(0, 229, 255, 0.6);
          animation: bracketIn 0.8s ease-out 0.4s forwards;
          opacity: 0;
        }
        .b-tl { top: 0; left: 0; border-right: none; border-bottom: none; transform: translate(6px, 6px); }
        .b-tr { top: 0; right: 0; border-left: none; border-bottom: none; transform: translate(-6px, 6px); }
        .b-bl { bottom: 0; left: 0; border-right: none; border-top: none; transform: translate(6px, -6px); }
        .b-br { bottom: 0; right: 0; border-left: none; border-top: none; transform: translate(-6px, -6px); }

        @keyframes bracketIn { to { opacity: 1; transform: translate(0, 0); } }

        .ls-content {
          margin-top: 24px;
          text-align: center;
          display: flex;
          flex-direction: column;
          align-items: center;
        }

        .ls-title {
          font-family: 'Inter', sans-serif;
          font-size: 1.1rem;
          font-weight: 900;
          color: #00e5ff;
          text-transform: uppercase;
          letter-spacing: 0.4em;
          text-shadow: 0 0 30px rgba(0, 229, 255, 0.5);
          opacity: 0;
          animation: textIn 0.8s ease-out 1s forwards;
          margin-bottom: 8px;
        }

        .ls-subtitle {
          font-family: 'Inter', sans-serif;
          font-size: 0.65rem;
          color: rgba(255, 255, 255, 0.5);
          text-transform: uppercase;
          letter-spacing: 0.25em;
          opacity: 0;
          animation: textIn 0.8s ease-out 1.4s forwards;
          margin-bottom: 32px;
        }

        @keyframes textIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

        .ls-bar-track {
          width: 200px;
          height: 2px;
          background: rgba(255, 255, 255, 0.08);
          border-radius: 2px;
          overflow: hidden;
          opacity: 0;
          animation: textIn 0.5s ease-out 1.8s forwards;
        }
        .ls-bar-fill {
          height: 100%;
          background: linear-gradient(90deg, #00e5ff, #00ff88);
          box-shadow: 0 0 12px #00e5ff, 0 0 4px #00ff88;
          width: 0%;
          animation: barFill 4.0s ease-in-out 1.8s forwards;
        }
        @keyframes barFill { to { width: 100%; } }

        .ls-status-text {
          font-family: 'Inter', sans-serif;
          font-size: 0.6rem;
          letter-spacing: 0.2em;
          text-transform: uppercase;
          color: rgba(0, 229, 255, 0.7);
          font-weight: 400;
          margin-top: 16px;
          height: 1rem;
          transition: opacity 0.3s ease-in-out;
        }

        .ls-scanner-container {
          width: 280px;
          height: 60px;
          overflow: hidden;
          position: relative;
          margin-top: 48px;
        }
        .ls-scan-line {
          position: absolute;
          width: 1px;
          height: 60px;
          background: linear-gradient(180deg, transparent, #00e5ff, transparent);
          left: -100px;
          animation: scanLine 2s ease-in-out 1.8s forwards;
        }
        @keyframes scanLine { to { left: 300px; } }
      `}</style>

      <svg className="ls-particles" viewBox="0 0 1000 1000" preserveAspectRatio="none">
        <circle className="particle" cx="100" cy="200" r="1.5" style={{ animationDelay: "0.2s" }} />
        <circle className="particle" cx="800" cy="150" r="1.2" style={{ animationDelay: "1.5s" }} />
        <circle className="particle" cx="450" cy="800" r="2.0" style={{ animationDelay: "3.2s" }} />
        <circle className="particle" cx="200" cy="700" r="1.0" style={{ animationDelay: "0.8s" }} />
        <circle className="particle" cx="700" cy="300" r="1.8" style={{ animationDelay: "2.1s" }} />
        <circle className="particle" cx="300" cy="400" r="1.4" style={{ animationDelay: "0.5s" }} />
        <circle className="particle" cx="900" cy="600" r="1.6" style={{ animationDelay: "2.8s" }} />
        <circle className="particle" cx="150" cy="900" r="1.3" style={{ animationDelay: "1.2s" }} />
        <circle className="particle" cx="600" cy="850" r="1.1" style={{ animationDelay: "3.7s" }} />
        <circle className="particle" cx="500" cy="100" r="1.7" style={{ animationDelay: "1.9s" }} />
        <circle className="particle" cx="50" cy="500" r="1.5" style={{ animationDelay: "0.6s" }} />
        <circle className="particle" cx="950" cy="250" r="1.2" style={{ animationDelay: "2.4s" }} />
        <circle className="particle" cx="350" cy="50" r="2.0" style={{ animationDelay: "0.1s" }} />
        <circle className="particle" cx="750" cy="750" r="1.0" style={{ animationDelay: "1.1s" }} />
        <circle className="particle" cx="400" cy="450" r="1.8" style={{ animationDelay: "2.6s" }} />
        <circle className="particle" cx="850" cy="950" r="1.4" style={{ animationDelay: "3.4s" }} />
        <circle className="particle" cx="250" cy="150" r="1.6" style={{ animationDelay: "0.9s" }} />
        <circle className="particle" cx="650" cy="550" r="1.3" style={{ animationDelay: "1.7s" }} />
        <circle className="particle" cx="120" cy="350" r="1.9" style={{ animationDelay: "2.9s" }} />
        <circle className="particle" cx="550" cy="650" r="1.1" style={{ animationDelay: "0.4s" }} />
      </svg>

      <div className="ls-overlay"></div>

      <div className="ls-logo-wrapper">
        <div className="bracket b-tl"></div>
        <div className="bracket b-tr"></div>
        <div className="bracket b-bl"></div>
        <div className="bracket b-br"></div>
        <img src="/logo.png" alt="Logo" className="ls-logo" />
      </div>

      <div className="ls-content">
        <h1 className="ls-title">GABESI AIGUARDIAN</h1>
        <p className="ls-subtitle">ENVIRONMENTAL INTELLIGENCE PLATFORM</p>

        <div className="ls-bar-track">
          <div className="ls-bar-fill"></div>
        </div>

        <p className="ls-status-text" style={{ opacity: messageVisible ? 1 : 0 }}>
          {currentMessage}
        </p>

        <div className="ls-scanner-container">
          <div className="ls-scan-line"></div>
        </div>
      </div>
    </div>
  );
}
