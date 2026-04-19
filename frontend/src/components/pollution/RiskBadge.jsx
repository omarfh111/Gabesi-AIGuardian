import React from 'react';
import { Badge, Card, CardContent } from '../ui';

const RISK_CONFIG = {
  low: { label: 'Healthy environment', badge: 'low', progress: 25 },
  moderate: { label: 'Caution advised', badge: 'medium', progress: 50 },
  high: { label: 'High exposure', badge: 'high', progress: 75 },
  critical: { label: 'Severe risk', badge: 'high', progress: 100 },
};

const RiskBadge = ({ level }) => {
  const key = level?.toLowerCase();
  const config = RISK_CONFIG[key] || { label: 'Unknown status', badge: 'neutral', progress: 0 };

  return (
    <Card className="rounded-xl">
      <CardContent className="space-y-3 p-5">
        <div className="flex items-center justify-between">
          <p className="text-xs text-gray-500">Pollution Risk Index</p>
          <Badge variant={config.badge}>{level || 'unknown'}</Badge>
        </div>
        <p className="text-sm font-medium text-gray-800">{config.label}</p>
        <div className="h-2 w-full rounded-full bg-gray-100">
          <div
            className={`h-2 rounded-full ${config.badge === 'high' ? 'bg-red-500' : config.badge === 'medium' ? 'bg-amber-500' : 'bg-emerald-500'}`}
            style={{ width: `${config.progress}%` }}
          />
        </div>
      </CardContent>
    </Card>
  );
};

export default RiskBadge;
