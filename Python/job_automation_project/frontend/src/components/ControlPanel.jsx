import { useState } from 'react';
import { startBot, stopBot } from '../api/client';

/**
 * ControlPanel — Bot start/stop controls with search query input.
 *
 * @param {{
 *   botStatus: string,
 *   currentRun: object|null,
 *   onStatusChange: function
 * }} props
 */
export default function ControlPanel({ botStatus, currentRun, onStatusChange }) {
  const [searchQuery, setSearchQuery] = useState('AI Engineer,Machine Learning Engineer');
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  const isRunning = botStatus === 'RUNNING';
  const isStopping = botStatus === 'STOPPING';
  const isIdle = botStatus === 'IDLE';

  const handleStart = async () => {
    setError(null);
    setActionLoading(true);
    try {
      await startBot(searchQuery);
      onStatusChange?.();
    } catch (err) {
      const msg = err.response?.data?.error || err.message || 'Failed to start bot';
      setError(msg);
    } finally {
      setActionLoading(false);
    }
  };

  const handleStop = async () => {
    setError(null);
    setActionLoading(true);
    try {
      await stopBot();
      onStatusChange?.();
    } catch (err) {
      setError(err.message || 'Failed to stop bot');
    } finally {
      setActionLoading(false);
    }
  };

  // Calculate run duration
  const getRunDuration = () => {
    if (!currentRun?.started_at) return null;
    const start = new Date(currentRun.started_at);
    const now = currentRun.ended_at ? new Date(currentRun.ended_at) : new Date();
    const diffSec = Math.floor((now - start) / 1000);
    const h = Math.floor(diffSec / 3600);
    const m = Math.floor((diffSec % 3600) / 60);
    const s = diffSec % 60;
    if (h > 0) return `${h}h ${m}m ${s}s`;
    if (m > 0) return `${m}m ${s}s`;
    return `${s}s`;
  };

  return (
    <div className="card">
      <div className="card__title">Bot Control</div>

      <div className="control-panel">
        {/* Search query input */}
        <div className="control-panel__input-group">
          <label className="control-panel__label" htmlFor="search-query">
            Search Keywords
          </label>
          <input
            id="search-query"
            className="control-panel__input"
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="AI Engineer, Machine Learning Engineer"
            disabled={!isIdle}
          />
        </div>

        {/* Action button */}
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: '12px', paddingTop: '20px' }}>
          {isIdle ? (
            <button
              id="btn-start-bot"
              className="btn btn--start"
              onClick={handleStart}
              disabled={actionLoading || !searchQuery.trim()}
            >
              {actionLoading ? '⏳ Starting...' : '▶ Start Bot'}
            </button>
          ) : (
            <button
              id="btn-stop-bot"
              className="btn btn--stop"
              onClick={handleStop}
              disabled={actionLoading || isStopping}
            >
              {isStopping ? '⏳ Stopping...' : '■ Stop Bot'}
            </button>
          )}
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div style={{
          marginTop: '12px',
          padding: '10px 14px',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.2)',
          borderRadius: '8px',
          color: '#fca5a5',
          fontSize: '0.85rem',
        }}>
          ⚠ {error}
        </div>
      )}

      {/* Active run summary */}
      {currentRun && (isRunning || isStopping) && (
        <div className="run-summary" style={{ marginTop: '16px' }}>
          <div className="run-summary__item">
            <span className="run-summary__label">Run ID</span>
            <span className="run-summary__value">#{currentRun.id}</span>
          </div>
          <div className="run-summary__item">
            <span className="run-summary__label">Duration</span>
            <span className="run-summary__value">{getRunDuration()}</span>
          </div>
          <div className="run-summary__item">
            <span className="run-summary__label">Processed</span>
            <span className="run-summary__value">{currentRun.total_processed}</span>
          </div>
          <div className="run-summary__item">
            <span className="run-summary__label">Applied</span>
            <span className="run-summary__value" style={{ color: '#22c55e' }}>
              {currentRun.total_applied}
            </span>
          </div>
          <div className="run-summary__item">
            <span className="run-summary__label">Query</span>
            <span className="run-summary__value" style={{ fontSize: '0.8rem' }}>
              {currentRun.search_query}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
