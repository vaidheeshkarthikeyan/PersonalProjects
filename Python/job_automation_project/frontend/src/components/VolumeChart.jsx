import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

/**
 * VolumeChart — 7-day trailing stacked bar chart of application volume.
 *
 * @param {{ data: Array|null, loading: boolean }} props
 */
export default function VolumeChart({ data, loading }) {
  const chartData = data || [];

  // Format date labels (e.g., "2025-01-15" → "Jan 15")
  const formatDate = (dateStr) => {
    const d = new Date(dateStr + 'T00:00:00');
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <div className="card chart-card">
      <div className="chart-card__header">
        <div className="chart-card__title">Application Volume</div>
        <div className="chart-card__subtitle">7-day trailing breakdown</div>
      </div>

      {loading ? (
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: '12px', height: '280px', padding: '20px 0' }}>
          {[...Array(7)].map((_, i) => (
            <div
              key={i}
              className="skeleton"
              style={{
                flex: 1,
                height: `${40 + Math.random() * 60}%`,
                borderRadius: '6px 6px 0 0',
              }}
            />
          ))}
        </div>
      ) : chartData.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state__icon">📈</div>
          <div className="empty-state__text">No application data yet</div>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 5 }}>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(99, 102, 241, 0.08)"
              vertical={false}
            />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              tick={{ fill: '#64748b', fontSize: 12 }}
              axisLine={{ stroke: 'rgba(99, 102, 241, 0.12)' }}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: '#64748b', fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              allowDecimals={false}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(99, 102, 241, 0.06)' }} />
            <Legend
              wrapperStyle={{ fontSize: '12px', color: '#94a3b8' }}
              iconType="circle"
              iconSize={8}
            />
            <Bar
              dataKey="applied"
              name="Applied"
              stackId="stack"
              fill="#22c55e"
              radius={[0, 0, 0, 0]}
            />
            <Bar
              dataKey="skipped"
              name="Skipped"
              stackId="stack"
              fill="#f59e0b"
              radius={[0, 0, 0, 0]}
            />
            <Bar
              dataKey="failed"
              name="Failed"
              stackId="stack"
              fill="#ef4444"
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}

/** Custom glassmorphism-styled tooltip for the chart. */
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload || payload.length === 0) return null;

  const formatDate = (dateStr) => {
    const d = new Date(dateStr + 'T00:00:00');
    return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  };

  const colorMap = {
    applied: '#22c55e',
    skipped: '#f59e0b',
    failed: '#ef4444',
  };

  return (
    <div className="custom-tooltip">
      <div className="custom-tooltip__label">{formatDate(label)}</div>
      {payload.map((entry) => (
        <div key={entry.dataKey} className="custom-tooltip__entry">
          <span
            className="custom-tooltip__dot"
            style={{ background: colorMap[entry.dataKey] || entry.color }}
          />
          <span>{entry.name}: <strong>{entry.value}</strong></span>
        </div>
      ))}
    </div>
  );
}
