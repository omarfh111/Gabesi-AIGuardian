import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { AlertTriangle, BookOpen, CheckCircle2, ChevronDown, ChevronUp, XCircle } from 'lucide-react';

const DiagnosisCard = ({ data }) => {
  const { t } = useTranslation();
  const [showSources, setShowSources] = useState(false);

  const severityColors = {
    low: 'bg-green-500/10 text-green-400 border-green-500/20',
    medium: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
    high: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
    critical: 'bg-red-500/10 text-red-400 border-red-500/20',
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-start gap-2">
        <h3 className="font-black text-lg leading-tight uppercase text-accent tracking-tighter">
          {data.probable_cause}
        </h3>
        <span className={`px-2 py-1 rounded text-[10px] font-black uppercase tracking-widest border shrink-0 ${severityColors[data.severity] || 'bg-white/10'}`}>
          {data.severity}
        </span>
      </div>

      <div className="space-y-1">
        <div className="flex justify-between text-[10px] text-text-muted font-black uppercase tracking-widest">
          <span>AI Confidence Level</span>
          <span className="text-text-secondary">{Math.round(data.confidence * 100)}%</span>
        </div>
        <div className="w-full bg-white/5 rounded-full h-1 mt-1 overflow-hidden">
          <div 
            className="bg-accent h-full transition-all duration-1000 shadow-[0_0_10px_#06b6d4]" 
            style={{ width: `${data.confidence * 100}%` }}
          />
        </div>
      </div>

      {data.pollution_link && (
        <div className="flex items-center gap-3 bg-red-500/10 text-red-400 px-3 py-2.5 rounded-xl border border-red-500/20">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <span className="text-xs font-black uppercase tracking-widest">Pollution Link Detected</span>
        </div>
      )}

      <div className="rounded-r-xl border-l-4 border-sky-500 bg-sky-50 p-3">
        <span className="text-[10px] font-black text-accent block mb-1 uppercase tracking-widest">
          {t('common.recommendedAction')}
        </span>
        <p className="text-sm leading-relaxed text-gray-900">{data.recommended_action}</p>
      </div>

      <div className="flex items-center justify-between pt-4 border-t border-white/10 text-[10px]">
        <div className="flex items-center gap-2 font-black uppercase tracking-widest">
          {data.faithfulness_verified ? (
            <CheckCircle2 className="w-4 h-4 text-green-400" />
          ) : (
            <XCircle className="w-4 h-4 text-orange-400" />
          )}
          <span className={data.faithfulness_verified ? 'text-green-400' : 'text-orange-400'}>
            {data.faithfulness_verified ? 'Grounded in evidence' : 'Requires verification'}
          </span>
        </div>

        <button 
          onClick={() => setShowSources(!showSources)}
          className="flex items-center gap-1.5 text-accent hover:text-accent/80 font-black uppercase tracking-widest transition-colors"
        >
          <BookOpen className="w-3.5 h-3.5" />
          {t('common.sources')} ({data.sources?.length || 0})
          {showSources ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      {showSources && data.sources?.length > 0 && (
        <ul className="text-[11px] text-text-muted space-y-2 pl-1 pt-3 border-t border-white/5 animate-in fade-in slide-in-from-top-1">
          {data.sources.map((source, idx) => (
            <li key={idx} className="flex gap-2">
              <span className="text-accent">•</span>
              {source}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default DiagnosisCard;
