import { useState } from 'react';
import Dashboard from './pages/Dashboard';
import './index.css';

/**
 * App — Root component with navigation bar and dashboard.
 */
export default function App() {
  const [botStatus, setBotStatus] = useState('IDLE');

  const statusLabel = {
    IDLE: 'Idle',
    RUNNING: 'Running',
    STOPPING: 'Stopping...',
  };

  const statusDotClass = `navbar__status-dot${
    botStatus === 'RUNNING'
      ? ' navbar__status-dot--running'
      : botStatus === 'STOPPING'
        ? ' navbar__status-dot--stopping'
        : ''
  }`;

  return (
    <>
      {/* Navigation Bar */}
      <nav className="navbar">
        <div className="navbar__brand">
          <div className="navbar__brand-icon">⚡</div>
          <span>LinkedIn AutoApply</span>
        </div>
        <div className="navbar__status">
          <div className={statusDotClass} />
          <span>Engine: {statusLabel[botStatus] || 'Idle'}</span>
        </div>
      </nav>

      {/* Main Content */}
      <main className="app-container">
        <Dashboard onBotStatusChange={setBotStatus} />
      </main>
    </>
  );
}
