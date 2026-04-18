import React, { useState } from 'react';
import { useAppStore } from '../store';
import { Filter, ChevronDown, ChevronUp } from 'lucide-react';

const ISSUE_TYPES = [
  { value: '', label: 'All Types', color: 'bg-gray-400' },
  { value: 'smoke', label: '🔥 Smoke / Air', color: 'bg-red-500' },
  { value: 'smell', label: '👃 Chemical Smell', color: 'bg-purple-500' },
  { value: 'dust', label: '🌫️ Dust', color: 'bg-yellow-500' },
  { value: 'water', label: '💧 Water', color: 'bg-blue-500' },
  { value: 'waste', label: '🗑️ Waste', color: 'bg-green-600' },
  { value: 'symptoms', label: '🩺 Symptoms', color: 'bg-orange-500' },
];

const SEVERITIES = [
  { value: '', label: 'All' },
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
];

export default function FiltersPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const filters = useAppStore((s) => s.filters);
  const setFilter = useAppStore((s) => s.setFilter);
  const reports = useAppStore((s) => s.reports);

  return (
    <div className="absolute bottom-6 left-4 z-[1000] w-72">
      {/* Toggle button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 bg-white/95 backdrop-blur-md shadow-lg rounded-xl px-4 py-2.5 border border-gray-200/60 hover:shadow-xl transition-all duration-200 w-full"
      >
        <Filter size={16} className="text-gabes-500" />
        <span className="text-sm font-semibold text-gray-700 flex-1 text-left">
          Filters
        </span>
        <span className="text-xs bg-gabes-100 text-gabes-900 px-2 py-0.5 rounded-full font-medium">
          {reports.length} reports
        </span>
        {isOpen ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
      </button>

      {/* Panel */}
      {isOpen && (
        <div className="mt-2 bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl border border-gray-200/60 p-4 space-y-4 animate-in slide-in-from-bottom-2 duration-200">
          {/* Issue Type */}
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 block">
              Issue Type
            </label>
            <div className="flex flex-wrap gap-1.5">
              {ISSUE_TYPES.map((type) => (
                <button
                  key={type.value}
                  onClick={() => setFilter('issueType', type.value || null)}
                  className={`text-xs px-3 py-1.5 rounded-full border transition-all duration-150 font-medium ${
                    (filters.issueType || '') === type.value
                      ? 'bg-gabes-500 text-white border-gabes-500 shadow-md shadow-gabes-500/20'
                      : 'bg-gray-50 text-gray-600 border-gray-200 hover:border-gabes-300 hover:bg-gabes-50'
                  }`}
                >
                  {type.label}
                </button>
              ))}
            </div>
          </div>

          {/* Severity */}
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 block">
              Severity
            </label>
            <div className="flex gap-1.5">
              {SEVERITIES.map((sev) => (
                <button
                  key={sev.value}
                  onClick={() => setFilter('severity', sev.value || null)}
                  className={`text-xs px-3 py-1.5 rounded-full border transition-all duration-150 font-medium flex-1 ${
                    (filters.severity || '') === sev.value
                      ? 'bg-gabes-500 text-white border-gabes-500 shadow-md shadow-gabes-500/20'
                      : 'bg-gray-50 text-gray-600 border-gray-200 hover:border-gabes-300 hover:bg-gabes-50'
                  }`}
                >
                  {sev.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
