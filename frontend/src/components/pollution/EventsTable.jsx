import React from 'react';
import Badge from '../ui/Badge';

const EventsTable = ({ events }) => {
  if (!events || events.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-gray-300 bg-gray-50 py-8 text-center text-sm text-gray-500">
        No recent pollution events recorded.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-gray-200">
      <table className="w-full border-collapse text-left">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-xs text-gray-500">Event Date</th>
            <th className="px-4 py-3 text-xs text-gray-500">Pollutant</th>
            <th className="px-4 py-3 text-xs text-gray-500">Severity</th>
            <th className="px-4 py-3 text-xs text-gray-500">Origin</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 bg-white">
          {events.map((event, idx) => (
            <tr key={idx} className="hover:bg-gray-50/80">
              <td className="px-4 py-3 text-sm text-gray-700">
                {new Date(event.event_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
              </td>
              <td className="px-4 py-3 text-sm font-medium text-gray-800">{event.pollutant}</td>
              <td className="px-4 py-3">
                <Badge variant={event.severity === 'severe' ? 'high' : 'medium'}>{event.severity}</Badge>
              </td>
              <td className="px-4 py-3 text-sm text-gray-600">{event.temporal_type}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default EventsTable;
