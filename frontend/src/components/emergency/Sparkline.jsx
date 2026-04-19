import React from 'react';

const Sparkline = ({ data, color = '#06b6d4', width = 280, height = 28 }) => {
  if (!data || data.length === 0) return null;

  const values = data.map(d => d.co2 ?? d);
  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = max - min || 1;
  const padding = 2;
  const step = (width - padding * 2) / (values.length - 1);

  const points = values.map((v, i) => {
    const x = padding + i * step;
    const y = height - padding - ((v - min) / range) * (height - padding * 2);
    return `${x},${y}`;
  }).join(' ');

  const firstX = padding;
  const lastX = padding + (values.length - 1) * step;
  const areaPoints = `${firstX},${height} ${points} ${lastX},${height}`;
  const gradId = `grad-${color.replace('#', '')}`;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      style={{ width: '100%', height: `${height}px` }}
    >
      <defs>
        <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0.02" />
        </linearGradient>
      </defs>
      <polygon points={areaPoints} fill={`url(#${gradId})`} />
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};

export default Sparkline;
