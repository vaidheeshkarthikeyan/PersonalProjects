import { useState, useEffect, useCallback, useRef } from 'react';
import { fetchKpis, fetchVolume, getBotStatus } from '../api/client';
import KpiCards from '../components/KpiCards';
import VolumeChart from '../components/VolumeChart';
import ApplicationTable from '../components/ApplicationTable';
import ControlPanel from '../components/ControlPanel';

/**
 * Dashboard — Main page composing all dashboard components.
 *
 * Layout:
 * - Top row: Control Panel (full width)
 * - Second row: 4 × KPI Cards
 * - Third row: Volume Chart (2/3) + Run Summary (1/3) — handled by chart row
 * - Bottom row: Application Table (full width)
 *
 * Polling:
 * - 5s when bot is running (fast updates)
 * - 30s when idle (background refresh)
 *
 * @param {{ onBotStatusChange: function }} props
 */
export default function Dashboard({ onBotStatusChange }) {
  const [kpis, setKpis] = useState(null);
  const [volume, setVolume] = useState(null);
  const [botStatus, setBotStatus] = useState('IDLE');
  const [currentRun, setCurrentRun] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const intervalRef = useRef(null);

  // Fetch all dashboard data
  const loadDashboardData = useCallback(async () => {
    try {
      const [kpiData, volumeData, statusData] = await Promise.all([
        fetchKpis(),
        fetchVolume(),
        getBotStatus(),
      ]);

      setKpis(kpiData);
      setVolume(volumeData);
      setBotStatus(statusData.bot_status || 'IDLE');
      setCurrentRun(statusData.current_run);
      onBotStatusChange?.(statusData.bot_status || 'IDLE');
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  }, [onBotStatusChange]);

  // Initial load
  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  // Polling — adjust interval based on bot status
  useEffect(() => {
    const interval = botStatus === 'RUNNING' || botStatus === 'STOPPING'
      ? 5000   // 5s when bot is active
      : 30000; // 30s when idle

    intervalRef.current = setInterval(() => {
      loadDashboardData();
      setRefreshTrigger((prev) => prev + 1);
    }, interval);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [botStatus, loadDashboardData]);

  // Force refresh when bot status changes (start/stop actions)
  const handleStatusChange = () => {
    setTimeout(() => {
      loadDashboardData();
      setRefreshTrigger((prev) => prev + 1);
    }, 1000);
  };

  return (
    <div className="dashboard">
      {/* Control Panel */}
      <ControlPanel
        botStatus={botStatus}
        currentRun={currentRun}
        onStatusChange={handleStatusChange}
      />

      {/* KPI Cards */}
      <KpiCards kpis={kpis} loading={loading} />

      {/* Chart Row */}
      <div className="dashboard__chart-row">
        <VolumeChart data={volume} loading={loading} />

        {/* Run Summary Side Panel */}
        <div className="card">
          <div className="chart-card__header">
            <div className="chart-card__title">Latest Run</div>
            <div className="chart-card__subtitle">Most recent session details</div>
          </div>

          {currentRun ? (
            <div className="run-summary">
              <div className="run-summary__item">
                <span className="run-summary__label">Status</span>
                <span className={`badge badge--${(currentRun.status || '').toLowerCase() === 'running' ? 'success' : currentRun.status?.toLowerCase() === 'errored' ? 'failed' : 'skipped'}`}>
                  {currentRun.status}
                </span>
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
                <span className="run-summary__label">Skipped</span>
                <span className="run-summary__value" style={{ color: '#f59e0b' }}>
                  {currentRun.total_skipped}
                </span>
              </div>
              <div className="run-summary__item">
                <span className="run-summary__label">Failed</span>
                <span className="run-summary__value" style={{ color: '#ef4444' }}>
                  {currentRun.total_failed}
                </span>
              </div>
              {currentRun.error_message && (
                <div style={{
                  padding: '8px 12px',
                  background: 'rgba(239, 68, 68, 0.1)',
                  borderRadius: '8px',
                  color: '#fca5a5',
                  fontSize: '0.8rem',
                  marginTop: '8px',
                }}>
                  {currentRun.error_message}
                </div>
              )}
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-state__icon">🤖</div>
              <div className="empty-state__text">No runs yet</div>
            </div>
          )}
        </div>
      </div>

      {/* Application Table */}
      <ApplicationTable refreshTrigger={refreshTrigger} />
    </div>
  );
}
