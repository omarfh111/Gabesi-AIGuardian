import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const TrendChart = ({ events }) => {
  if (!events || events.length === 0) return (
    <div className="h-64 flex items-center justify-center text-gray-400 text-sm italic">
      No trend data available for the selected period.
    </div>
  );

  // Filter for SO2 events, map to chart format, and sort chronologically
  const chartData = events
    .filter(e => e.pollutant === 'SO2')
    .map(e => ({
      date: e.event_date,
      displayDate: new Date(e.event_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
      value: parseFloat(e.daily_mean_ug_m3 || 0)
    }))
    .sort((a, b) => new Date(a.date) - new Date(b.date));

  if (chartData.length === 0) return (
    <div className="h-64 flex items-center justify-center text-gray-400 text-sm italic">
      No SO₂ events in this period.
    </div>
  );

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-gray-900 text-white p-3 rounded-lg shadow-xl border border-gray-800">
          <p className="text-[10px] uppercase font-bold text-gray-400 mb-1">{label}</p>
          <p className="text-sm font-black">
            {payload[0].value} <span className="text-[10px] font-normal text-gray-400">µg/m³</span>
          </p>
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
              <stop offset="5%" stopColor="#f4a261" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#f4a261" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
          <XAxis 
            dataKey="displayDate" 
            tick={{ fontSize: 10, fill: '#9ca3af', fontWeight: 600 }} 
            axisLine={false} 
            tickLine={false} 
            dy={10}
          />
          <YAxis 
            tick={{ fontSize: 10, fill: '#9ca3af', fontWeight: 600 }} 
            axisLine={false} 
            tickLine={false} 
            dx={-10}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area 
            type="monotone" 
            dataKey="value" 
            stroke="#f4a261" 
            strokeWidth={3} 
            fillOpacity={1} 
            fill="url(#colorValue)" 
            activeDot={{ r: 6, strokeWidth: 0, fill: '#e63946' }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default TrendChart;
