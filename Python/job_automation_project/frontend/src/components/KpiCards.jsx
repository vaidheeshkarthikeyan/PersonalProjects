import { useState, useEffect } from 'react';

/**
 * KpiCards — Four glassmorphism cards showing lifetime KPIs.
 *
 * - Total Processed (indigo accent)
 * - Submitted / Applied (green)
 * - Skipped (amber)
 * - Failed (red)
 *
 * @param {{ kpis: object|null, loading: boolean }} props
 */
export default function KpiCards({ kpis, loading }) {
  const cards = [
    {
      label: 'Total Processed',
      key: 'total_processed',
      variant: '',
      icon: '📊',
    },
    {
      label: 'Submitted',
      key: 'total_applied',
      variant: 'success',
      icon: '✓',
    },
    {
      label: 'Skipped',
      key: 'total_skipped',
      variant: 'warning',
      icon: '⊘',
    },
    {
      label: 'Failed',
      key: 'total_failed',
      variant: 'error',
      icon: '✗',
    },
  ];

  return (
    <div className="dashboard__kpi-row">
      {cards.map((card) => (
        <KpiCard
          key={card.key}
          label={card.label}
          value={kpis ? kpis[card.key] : 0}
          variant={card.variant}
          icon={card.icon}
          loading={loading}
        />
      ))}
    </div>
  );
}

function KpiCard({ label, value, variant, icon, loading }) {
  const [displayValue, setDisplayValue] = useState(0);

  // Animated counter effect
  useEffect(() => {
    if (loading || value === undefined) return;

    const target = Number(value) || 0;
    if (target === 0) {
      setDisplayValue(0);
      return;
    }

    const duration = 600; // ms
    const steps = 30;
    const increment = target / steps;
    let current = 0;
    let step = 0;

    const timer = setInterval(() => {
      step++;
      current = Math.min(Math.round(increment * step), target);
      setDisplayValue(current);
      if (step >= steps) {
        clearInterval(timer);
        setDisplayValue(target);
      }
    }, duration / steps);

    return () => clearInterval(timer);
  }, [value, loading]);

  const cardClass = `card kpi-card${variant ? ` kpi-card--${variant}` : ''}`;

  return (
    <div className={cardClass}>
      <div className="kpi-card__icon">{icon}</div>
      <div className="card__title">{label}</div>
      {loading ? (
        <div className="skeleton" style={{ width: '80px', height: '36px' }} />
      ) : (
        <div className="kpi-card__value">
          {displayValue.toLocaleString()}
        </div>
      )}
    </div>
  );
}
