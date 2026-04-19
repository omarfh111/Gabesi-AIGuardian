import React from 'react';

const RiskBadge = ({ level }) => {
  const configs = {
    low: { color: '#10b981', label: 'Healthy Environment' },
    moderate: { color: '#f59e0b', label: 'Caution Advised' },
    high: { color: '#ef4444', label: 'High Exposure' },
    critical: { color: '#ff0000', label: 'Severe Risk' },
  };

  const config = configs[level?.toLowerCase()] || { color: '#8b95b8', label: 'Unknown Status' };

  return (
    <div 
      className="glass-card p-6 flex flex-col items-center justify-center relative overflow-hidden h-full group transition-all duration-500"
      style={{ borderLeft: `4px solid ${config.color}` }}
    >
      <div 
        className="absolute top-0 right-0 w-32 h-32 blur-[80px] opacity-20 group-hover:opacity-40 transition-opacity"
        style={{ background: config.color }}
      />
      
      <span className="text-[10px] font-black text-text-muted uppercase tracking-[0.3em] mb-2">Pollution Risk Index</span>
      <span 
        className="text-4xl font-black uppercase tracking-tighter mb-1"
        style={{ color: config.color, textShadow: `0 0 20px ${config.color}40` }}
      >
        {level || 'Scanning...'}
      </span>
      <span className="text-[10px] font-bold text-text-secondary uppercase tracking-widest">{config.label}</span>
      
      {/* Animated progress bar below */}
      <div className="w-full h-1 bg-white/5 rounded-full mt-4 overflow-hidden">
        <div 
          className="h-full rounded-full transition-all duration-1000 ease-out"
          style={{ 
            width: level?.toLowerCase() === 'low' ? '25%' : level?.toLowerCase() === 'moderate' ? '50%' : level?.toLowerCase() === 'high' ? '75%' : '100%',
            backgroundColor: config.color,
            boxShadow: `0 0 10px ${config.color}`
          }}
        />
      </div>
    </div>
  );
};

export default RiskBadge;
