import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { BookOpen, Info, ChevronDown, ChevronUp } from 'lucide-react';

const PollutionQACard = ({ data }) => {
  const { t } = useTranslation();
  const [showSources, setShowSources] = useState(false);

  const confidenceColors = {
    high: 'bg-green-100 text-green-700',
    medium: 'bg-blue-100 text-blue-700',
    low: 'bg-orange-100 text-orange-700',
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="font-bold text-secondary text-base uppercase flex items-center gap-2">
          <Info className="w-4 h-4" />
          Pollution Insight
        </h3>
        <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-tighter ${confidenceColors[data.confidence] || 'bg-gray-100'}`}>
          {data.confidence} Confidence
        </span>
      </div>

      <div className="text-sm leading-relaxed text-gray-800 font-medium">
        {data.answer}
      </div>

      <div className="pt-2 border-t flex items-center justify-between">
        <button 
          onClick={() => setShowSources(!showSources)}
          className="flex items-center gap-1 text-xs text-secondary hover:underline font-bold"
        >
          <BookOpen className="w-3.5 h-3.5" />
          {t('common.sources')} ({data.sources?.length || 0})
          {showSources ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      {showSources && data.sources?.length > 0 && (
        <ul className="text-[10px] text-gray-500 space-y-1 animate-in fade-in">
          {data.sources.map((source, idx) => (
            <li key={idx} className="flex gap-1">
              <span>•</span>
              {source}
            </li>
          ))}
        </ul>
      )}

      {data.limitations && (
        <div className="text-[10px] text-gray-400 italic bg-gray-50 p-2 rounded border border-gray-100">
          <strong>Note:</strong> {data.limitations}
        </div>
      )}
    </div>
  );
};

export default PollutionQACard;
