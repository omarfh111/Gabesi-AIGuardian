import React, { useEffect, useState } from 'react';
import { fetchReportDetails, ReportDetails } from '../api';
import { Clock, AlertTriangle, Brain, Users, Loader2 } from 'lucide-react';

interface Props {
  reportId: string;
  issueType: string;
  createdAt: string;
  severity?: string;
  description?: string;
}

const RISK_COLORS: Record<string, string> = {
  high: 'bg-red-100 text-red-700',
  medium: 'bg-amber-100 text-amber-700',
  low: 'bg-green-100 text-green-700',
};

export default function ReportPopup({ reportId, issueType, createdAt, severity, description }: Props) {
  const [details, setDetails] = useState<ReportDetails | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchReportDetails(reportId)
      .then((data) => {
        if (!cancelled) setDetails(data);
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [reportId]);

  return (
    <div className="min-w-[260px] max-w-[300px] text-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-bold text-base capitalize text-gray-800">{issueType.replace('_', ' ')}</h3>
        {severity && (
          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase ${
            severity === 'high' ? 'bg-red-100 text-red-700' :
            severity === 'medium' ? 'bg-amber-100 text-amber-700' :
            'bg-green-100 text-green-700'
          }`}>
            {severity}
          </span>
        )}
      </div>

      {/* Timestamp */}
      <div className="flex items-center gap-1 text-gray-400 text-xs mb-2">
        <Clock size={12} />
        <span>{new Date(createdAt).toLocaleString()}</span>
      </div>

      {/* Description */}
      {description && (
        <p className="text-gray-600 text-xs mb-3 leading-relaxed border-l-2 border-gabes-200 pl-2">
          {description}
        </p>
      )}

      {/* AI Insights */}
      {loading ? (
        <div className="flex items-center justify-center py-3 text-gray-400">
          <Loader2 size={16} className="animate-spin mr-2" />
          <span className="text-xs">Fetching AI insights...</span>
        </div>
      ) : details ? (
        <div className="space-y-2 border-t border-gray-100 pt-2">
          {/* AI Summary */}
          {details.ai_summary && (
            <div className="flex gap-2">
              <Brain size={14} className="text-gabes-500 mt-0.5 shrink-0" />
              <p className="text-xs text-gray-600 leading-relaxed">{details.ai_summary}</p>
            </div>
          )}
          
          {/* Stats Row */}
          <div className="flex items-center gap-3 text-xs text-gray-500 pt-1">
            {details.similar_count > 0 && (
              <div className="flex items-center gap-1">
                <Users size={12} className="text-blue-500" />
                <span>{details.similar_count} similar</span>
              </div>
            )}
            {details.confidence_score > 0 && (
              <div className="flex items-center gap-1">
                <AlertTriangle size={12} className="text-amber-500" />
                <span>Conf: {Math.round(details.confidence_score * 100)}%</span>
              </div>
            )}
            {details.risk_level && (
              <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${
                RISK_COLORS[details.risk_level] || 'bg-gray-100 text-gray-600'
              }`}>
                {details.risk_level} risk
              </span>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
