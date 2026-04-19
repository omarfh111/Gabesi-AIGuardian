import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const TrendChart = ({ events }) => {
  if (!events || events.length === 0) return (
    <div className="h-64 flex items-center justify-center text-text-muted text-[10px] font-black uppercase tracking-widest italic">
      No trend data available for the selected period.
    </div>
  );

  const chartData = events
    .filter(e => e.pollutant === 'SO2')
    .map(e => ({
      date: e.event_date,
      displayDate: new Date(e.event_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
      value: parseFloat(e.daily_mean_ug_m3 || 0)
    }))
    .sort((a, b) => new Date(a.date) - new Date(b.date));

  if (chartData.length === 0) return (
    <div className="h-64 flex items-center justify-center text-text-muted text-[10px] font-black uppercase tracking-widest italic">
      No SO₂ events in this period.
    </div>
  );

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="glass-card bg-primary/95 p-3 shadow-2xl border-accent/20">
          <p className="text-[9px] uppercase font-black text-text-muted mb-2 tracking-widest">{label}</p>
          <div className="flex items-baseline gap-1">
             <span className="text-lg font-black text-accent">{payload[0].value}</span>
             <span className="text-[10px] font-bold text-text-muted uppercase">µg/m³</span>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 10, right: 10, bottom: 0, left: -20 }}>
          <defs>
            <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4}/>
              <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
          <XAxis 
            dataKey="displayDate" 
            tick={{ fontSize: 9, fill: '#4d567a', fontWeight: 800, letterSpacing: '0.05em' }} 
            axisLine={false} 
            tickLine={false} 
            dy={10}
          />
          <YAxis 
            tick={{ fontSize: 9, fill: '#4d567a', fontWeight: 800 }} 
            axisLine={false} 
            tickLine={false} 
            dx={-10}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'rgba(6,182,212,0.2)', strokeWidth: 2 }} />
          <Area 
            type="monotone" 
            dataKey="value" 
            stroke="#06b6d4" 
            strokeWidth={3} 
            fillOpacity={1} 
            fill="url(#colorValue)" 
            activeDot={{ r: 6, strokeWidth: 0, fill: '#06b6d4', shadow: '0 0 10px #06b6d4' }}
            animationDuration={1500}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default TrendChart;
