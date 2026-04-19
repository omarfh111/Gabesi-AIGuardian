import React from 'react';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const TrendChart = ({ events }) => {
  if (!events || events.length === 0) {
    return <div className="flex h-64 items-center justify-center text-sm text-gray-500">No trend data available.</div>;
  }

  const chartData = events
    .filter((e) => e.pollutant === 'SO2')
    .map((e) => ({
      date: e.event_date,
      displayDate: new Date(e.event_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
      value: parseFloat(e.daily_mean_ug_m3 || 0),
    }))
    .sort((a, b) => new Date(a.date) - new Date(b.date));

  if (chartData.length === 0) {
    return <div className="flex h-64 items-center justify-center text-sm text-gray-500">No SO2 events in this period.</div>;
  }

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 12, right: 12, bottom: 4, left: -20 }}>
          <defs>
            <linearGradient id="so2Fill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#0284c7" stopOpacity={0.35} />
              <stop offset="95%" stopColor="#0284c7" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
          <XAxis dataKey="displayDate" tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} />
          <Tooltip
            cursor={{ stroke: '#cbd5e1', strokeWidth: 1 }}
            contentStyle={{
              border: '1px solid #e5e7eb',
              borderRadius: '0.75rem',
              backgroundColor: '#ffffff',
              fontSize: '12px',
            }}
          />
          <Area type="monotone" dataKey="value" stroke="#0284c7" strokeWidth={2.5} fill="url(#so2Fill)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default TrendChart;
