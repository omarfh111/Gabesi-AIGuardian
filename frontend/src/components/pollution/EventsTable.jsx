import React from 'react';

const EventsTable = ({ events }) => {
  if (!events || events.length === 0) {
    return <div className="text-sm text-gray-500 py-4 text-center">No recent pollution events recorded.</div>;
  }

  const severityColors = {
    elevated: 'bg-yellow-100 text-yellow-800',
    severe: 'bg-red-100 text-red-800',
  };

  return (
    <div className="overflow-x-auto border border-gray-100 rounded-xl">
      <table className="w-full text-sm text-left">
        <thead className="bg-gray-50 text-gray-600 uppercase text-[10px] font-bold border-b border-gray-100">
          <tr>
            <th className="px-4 py-3">Date</th>
            <th className="px-4 py-3">Pollutant</th>
            <th className="px-4 py-3">Severity</th>
            <th className="px-4 py-3">Type</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {events.map((event, idx) => (
            <tr key={idx} className="bg-white hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3 whitespace-nowrap text-xs text-gray-500 font-medium">{event.date}</td>
              <td className="px-4 py-3 font-black uppercase text-gray-800">{event.pollutant}</td>
              <td className="px-4 py-3">
                <span className={`px-2 py-1 rounded-sm text-[10px] font-bold uppercase tracking-wider ${severityColors[event.severity] || 'bg-gray-100'}`}>
                  {event.severity}
                </span>
              </td>
              <td className="px-4 py-3 whitespace-nowrap text-[11px] font-medium text-gray-600">{event.type}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default EventsTable;
