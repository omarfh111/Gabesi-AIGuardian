import React from 'react';

const RiskBadge = ({ level }) => {
  const styles = {
    low: 'bg-green-100 text-green-800 border-green-200',
    moderate: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    high: 'bg-orange-100 text-orange-800 border-orange-200',
    critical: 'bg-red-100 text-red-800 border-red-200',
  };

  const currentStyle = styles[level?.toLowerCase()] || 'bg-gray-100 text-gray-800 border-gray-200';

  return (
    <div className={`px-4 py-3 rounded-xl border flex flex-col items-center justify-center h-full shadow-sm ${currentStyle}`}>
      <span className="text-[10px] font-bold uppercase tracking-widest opacity-80 mb-1">Exposure Risk</span>
      <span className="text-2xl font-black uppercase tracking-wider">{level || 'Unknown'}</span>
    </div>
  );
};

export default RiskBadge;
