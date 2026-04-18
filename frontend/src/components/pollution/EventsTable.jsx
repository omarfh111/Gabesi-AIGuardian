import React from 'react';

const EventsTable = ({ events }) => {
  if (!events || events.length === 0) {
    return (
      <div className="text-[10px] font-black uppercase tracking-widest text-text-muted py-8 text-center glass rounded-xl border-dashed">
        No recent pollution events recorded.
      </div>
    );
  }

  const severityColors = {
    elevated: 'text-warning bg-warning/10 border-warning/20',
    severe: 'text-danger bg-danger/10 border-danger/20',
  };

  const pollutantStyles = {
    SO2: 'text-accent shadow-[0_0_8px_rgba(6,182,212,0.3)]',
    NO2: 'text-purple shadow-[0_0_8px_rgba(139,92,246,0.3)]',
  };

  return (
    <div className="overflow-hidden rounded-xl border border-white/5">
      <table className="w-full text-left border-collapse">
        <thead className="glass border-b border-white/10">
          <tr>
            <th className="px-4 py-3 text-[9px] font-black uppercase tracking-[0.2em] text-text-muted">Event Date</th>
            <th className="px-4 py-3 text-[9px] font-black uppercase tracking-[0.2em] text-text-muted">Analyzed Data</th>
            <th className="px-4 py-3 text-[9px] font-black uppercase tracking-[0.2em] text-text-muted">Alert Level</th>
            <th className="px-4 py-3 text-[9px] font-black uppercase tracking-[0.2em] text-text-muted">Origin</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/[0.03]">
          {events.map((event, idx) => (
            <tr key={idx} className="hover:bg-white/[0.02] transition-all group">
              <td className="px-4 py-4 whitespace-nowrap">
                 <div className="flex flex-col">
                    <span className="text-[11px] font-bold text-text-primary">
                      {new Date(event.event_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                    </span>
                    <span className="text-[9px] text-text-muted font-bold uppercase tracking-tighter">Verified UTC</span>
                 </div>
              </td>
              <td className="px-4 py-4">
                 <div className="flex items-center gap-2">
                    <div className={`w-1.5 h-1.5 rounded-full animate-pulse ${event.pollutant === 'SO2' ? 'bg-accent' : 'bg-purple'}`} />
                    <span className={`text-sm font-black uppercase tracking-tighter ${pollutantStyles[event.pollutant] || 'text-text-primary'}`}>
                      {event.pollutant}
                    </span>
                 </div>
              </td>
              <td className="px-4 py-4">
                <span className={`px-2 py-1 rounded-md text-[9px] font-black uppercase tracking-widest border ${severityColors[event.severity] || 'bg-white/10 border-white/5'}`}>
                  {event.severity}
                </span>
              </td>
              <td className="px-4 py-4 whitespace-nowrap">
                 <span className="text-[10px] font-bold text-text-secondary bg-white/5 px-2 py-1 rounded-full uppercase tracking-widest border border-white/5 group-hover:border-accent/20 transition-colors">
                    {event.temporal_type}
                 </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default EventsTable;
