import { useEffect, useState } from 'react';
import { Brain, CalendarClock, Gauge, Users } from 'lucide-react';
import { Badge, Button, Card, CardContent, CardHeader, CardTitle } from '../ui';
import { getIssueMeta } from './issueMeta';

function getSeverityVariant(severity) {
  if (severity === 'high') return 'high';
  if (severity === 'medium') return 'medium';
  return 'low';
}

function getRiskVariant(riskLevel) {
  if (riskLevel === 'high') return 'high';
  if (riskLevel === 'medium') return 'medium';
  return 'low';
}

export default function MarkerPopup({ report, apiBase, onClose }) {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const meta = getIssueMeta(report.issue_type);

  useEffect(() => {
    let cancelled = false;

    fetch(`${apiBase}/reports/${report.id}`)
      .then((res) => res.json())
      .then((data) => {
        if (!cancelled) setDetails(data);
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [apiBase, report.id]);

  return (
    <div className="absolute right-4 top-20 z-10 w-[380px]">
      <Card className="rounded-xl bg-white/95 backdrop-blur">
        <CardHeader className="p-4 pb-3">
          <div className="flex items-start gap-3">
            <div className="rounded-lg bg-gray-100 p-2 text-gray-700">
              <meta.Icon className="h-4 w-4" />
            </div>
            <div className="min-w-0 flex-1">
              <CardTitle className="text-base font-medium capitalize text-gray-900">
                {meta.label} report
              </CardTitle>
              <p className="mt-0.5 flex items-center gap-1 text-xs text-gray-500">
                <CalendarClock className="h-3.5 w-3.5" />
                {new Date(report.created_at).toLocaleString()}
              </p>
            </div>
            <Button variant="secondary" size="sm" onClick={onClose}>
              Close
            </Button>
          </div>
        </CardHeader>

        <CardContent className="space-y-3 p-4 pt-0">
          <div className="flex items-center gap-2">
            <Badge variant={meta.badgeVariant}>{meta.label}</Badge>
            <Badge variant={getSeverityVariant(report.severity)}>{report.severity}</Badge>
          </div>

          {report.description ? (
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-3">
              <p className="text-sm text-gray-700">{report.description}</p>
            </div>
          ) : (
            <p className="text-sm text-gray-500">No user description provided.</p>
          )}

          <div className="rounded-lg border border-gray-100 p-3">
            <p className="mb-2 text-xs text-gray-500">AI summary</p>
            {loading ? (
              <div className="space-y-2">
                <div className="h-3 w-full animate-pulse rounded bg-gray-100" />
                <div className="h-3 w-2/3 animate-pulse rounded bg-gray-100" />
              </div>
            ) : details?.ai_summary ? (
              <p className="flex items-start gap-2 text-sm text-gray-700">
                <Brain className="mt-0.5 h-4 w-4 shrink-0 text-sky-700" />
                <span>{details.ai_summary}</span>
              </p>
            ) : (
              <p className="text-sm text-gray-500">No AI summary available.</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-2.5">
              <p className="mb-1 text-xs text-gray-500">Similar reports</p>
              <p className="flex items-center gap-1 text-sm font-medium text-gray-800">
                <Users className="h-3.5 w-3.5 text-gray-600" />
                {details?.similar_count || 0}
              </p>
            </div>
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-2.5">
              <p className="mb-1 text-xs text-gray-500">Confidence</p>
              <p className="flex items-center gap-1 text-sm font-medium text-gray-800">
                <Gauge className="h-3.5 w-3.5 text-gray-600" />
                {details?.confidence_score ? `${Math.round(details.confidence_score * 100)}%` : 'N/A'}
              </p>
            </div>
          </div>

          {details?.risk_level ? (
            <div className="flex items-center justify-between rounded-lg border border-gray-100 bg-gray-50 p-2.5">
              <p className="text-xs text-gray-600">Risk level</p>
              <Badge variant={getRiskVariant(details.risk_level)}>{details.risk_level}</Badge>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
