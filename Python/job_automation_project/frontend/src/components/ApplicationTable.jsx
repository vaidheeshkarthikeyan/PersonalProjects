import { useState, useEffect, useCallback } from 'react';
import { fetchLogs } from '../api/client';

/**
 * ApplicationTable — Filterable, paginated table of application log entries.
 *
 * Features:
 * - Status filter dropdown (All / Success / Skipped / Failed)
 * - Text search on company/title
 * - Pagination with previous/next
 * - Colour-coded status badges
 * - Row hover animation
 *
 * @param {{ refreshTrigger: number }} props
 */
export default function ApplicationTable({ refreshTrigger }) {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [perPage] = useState(15);
  const [statusFilter, setStatusFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [searchDebounce, setSearchDebounce] = useState('');

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearchDebounce(searchQuery);
      setPage(1); // Reset to page 1 on new search
    }, 400);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Fetch logs
  const loadLogs = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchLogs(
        page,
        perPage,
        statusFilter || null,
        searchDebounce || null
      );
      setLogs(data.items || []);
      setTotal(data.total || 0);
      setPages(data.pages || 1);
    } catch (err) {
      console.error('Failed to fetch logs:', err);
    } finally {
      setLoading(false);
    }
  }, [page, perPage, statusFilter, searchDebounce]);

  useEffect(() => {
    loadLogs();
  }, [loadLogs, refreshTrigger]);

  // Format timestamp for display
  const formatTimestamp = (ts) => {
    if (!ts) return '—';
    const d = new Date(ts);
    return d.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Status badge class
  const badgeClass = (status) => {
    const s = (status || '').toLowerCase();
    if (s === 'success') return 'badge badge--success';
    if (s === 'skipped') return 'badge badge--skipped';
    if (s === 'failed') return 'badge badge--failed';
    return 'badge';
  };

  return (
    <div className="card">
      <div className="card__title">Application Log</div>

      {/* Controls */}
      <div className="table-controls">
        <input
          id="log-search"
          className="table-controls__search"
          type="text"
          placeholder="Search company or title..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <select
          id="log-status-filter"
          className="table-controls__filter"
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
        >
          <option value="">All Statuses</option>
          <option value="SUCCESS">✓ Success</option>
          <option value="SKIPPED">⊘ Skipped</option>
          <option value="FAILED">✗ Failed</option>
        </select>
      </div>

      {/* Table */}
      <div className="table-wrapper">
        <table className="app-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Company</th>
              <th>Job Title</th>
              <th>Status</th>
              <th>Reason</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              // Skeleton rows
              [...Array(5)].map((_, i) => (
                <tr key={`skeleton-${i}`}>
                  {[...Array(5)].map((_, j) => (
                    <td key={j}>
                      <div
                        className="skeleton"
                        style={{ width: `${60 + Math.random() * 40}%`, height: '16px' }}
                      />
                    </td>
                  ))}
                </tr>
              ))
            ) : logs.length === 0 ? (
              <tr>
                <td colSpan="5">
                  <div className="empty-state">
                    <div className="empty-state__icon">📋</div>
                    <div className="empty-state__text">
                      {searchQuery || statusFilter
                        ? 'No results match your filters'
                        : 'No applications logged yet'}
                    </div>
                  </div>
                </td>
              </tr>
            ) : (
              logs.map((log) => (
                <tr key={log.id}>
                  <td>{formatTimestamp(log.timestamp)}</td>
                  <td title={log.company}>{log.company}</td>
                  <td title={log.job_title}>
                    {log.job_url ? (
                      <a href={log.job_url} target="_blank" rel="noopener noreferrer">
                        {log.job_title}
                      </a>
                    ) : (
                      log.job_title
                    )}
                  </td>
                  <td>
                    <span className={badgeClass(log.status)}>{log.status}</span>
                  </td>
                  <td title={log.failure_reason || ''}>{log.failure_reason || '—'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {!loading && pages > 1 && (
        <div className="pagination">
          <button
            className="pagination__btn"
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            ← Prev
          </button>
          <span>
            Page {page} of {pages} ({total} total)
          </span>
          <button
            className="pagination__btn"
            disabled={page >= pages}
            onClick={() => setPage((p) => Math.min(pages, p + 1))}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
