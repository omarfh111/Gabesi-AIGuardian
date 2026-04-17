import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { AlertTriangle, BookOpen, CheckCircle2, ChevronDown, ChevronUp, XCircle } from 'lucide-react';

const DiagnosisCard = ({ data }) => {
  const { t } = useTranslation();
  const [showSources, setShowSources] = useState(false);

  const severityColors = {
    low: 'bg-green-100 text-green-800',
    medium: 'bg-yellow-100 text-yellow-800',
    high: 'bg-orange-100 text-orange-800',
    critical: 'bg-red-100 text-red-800',
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-start gap-2">
        <h3 className="font-semibold text-lg leading-tight uppercase text-primary">
          {data.probable_cause}
        </h3>
        <span className={`px-2 py-1 rounded text-xs font-bold uppercase shrink-0 ${severityColors[data.severity] || 'bg-gray-100'}`}>
          {data.severity}
        </span>
      </div>

      <div className="space-y-1">
        <div className="flex justify-between text-xs text-gray-500 font-medium">
          <span>Confidence</span>
          <span>{Math.round(data.confidence * 100)}%</span>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-1.5 mt-1 overflow-hidden">
          <div 
            className="bg-accent h-full transition-all duration-1000" 
            style={{ width: `${data.confidence * 100}%` }}
          />
        </div>
      </div>

      {data.pollution_link && (
        <div className="flex items-center gap-2 bg-red-50 text-red-700 px-3 py-2 rounded-lg border border-red-100">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span className="text-sm font-bold">⚠️ Pollution Link Detected</span>
        </div>
      )}

      <div className="bg-primary/5 border-l-4 border-primary p-3 rounded-r-lg">
        <span className="text-xs font-bold text-primary block mb-1 uppercase tracking-wider">
          {t('common.recommendedAction')}
        </span>
        <p className="text-sm leading-relaxed">{data.recommended_action}</p>
      </div>

      <div className="flex items-center justify-between pt-2 border-t text-xs">
        <div className="flex items-center gap-1.5 font-medium">
          {data.faithfulness_verified ? (
            <CheckCircle2 className="w-4 h-4 text-green-600" />
          ) : (
            <XCircle className="w-4 h-4 text-orange-500" />
          )}
          <span className={data.faithfulness_verified ? 'text-green-800' : 'text-orange-700'}>
            {data.faithfulness_verified ? 'Grounded in evidence' : 'Requires verification'}
          </span>
        </div>

        <button 
          onClick={() => setShowSources(!showSources)}
          className="flex items-center gap-1 text-primary hover:underline font-bold"
        >
          <BookOpen className="w-3.5 h-3.5" />
          {t('common.sources')} ({data.sources?.length || 0})
          {showSources ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      {showSources && data.sources?.length > 0 && (
        <ul className="text-xs text-gray-600 space-y-1 pl-1 pt-1 border-t-0 animate-in fade-in slide-in-from-top-1">
          {data.sources.map((source, idx) => (
            <li key={idx} className="flex gap-2">
              <span className="text-primary opacity-50">•</span>
              {source}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default DiagnosisCard;
