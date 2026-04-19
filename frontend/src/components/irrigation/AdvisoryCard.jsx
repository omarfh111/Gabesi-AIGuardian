import React from 'react';
import { AlertTriangle, CloudSun, Droplet, Sun, Thermometer, Wind } from 'lucide-react';
import { Badge, Card, CardContent, CardHeader, CardTitle } from '../ui';

const AdvisoryCard = ({ data }) => {
  if (!data) return null;

  return (
    <Card className="h-full rounded-xl">
      <CardHeader className="p-6 pb-3">
        <div className="flex w-full items-start justify-between gap-4">
          <div>
            <CardTitle className="text-lg font-semibold text-gray-900">Irrigation Recommendation</CardTitle>
            <p className="mt-1 text-sm text-gray-600">Daily water requirement per square meter.</p>
          </div>
          <Badge variant="water" className="text-xs">
            <Droplet className="mr-1 h-3.5 w-3.5" />
            Precision model
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-5 p-6 pt-0">
        <div className="rounded-xl border border-blue-100 bg-blue-50 p-5 text-center">
          <p className="text-xs text-blue-700">Recommended Depth</p>
          <p className="mt-1 text-3xl font-semibold text-blue-900">
            {data.irrigation_depth_mm} <span className="text-base">mm</span>
          </p>
        </div>

        <div className="rounded-xl border border-gray-100 bg-gray-50 p-4">
          <p className="text-sm text-gray-700">{data.advisory_text}</p>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-lg border border-gray-100 p-3">
            <p className="text-xs text-gray-500">ET0</p>
            <p className="text-sm font-medium text-gray-900">{data.et0_mm_day} mm/day</p>
          </div>
          <div className="rounded-lg border border-gray-100 p-3">
            <p className="text-xs text-gray-500">Kc</p>
            <p className="text-sm font-medium text-gray-900">{data.kc}</p>
          </div>
        </div>

        {data.rs_estimated ? (
          <div className="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-amber-800">
            <AlertTriangle className="h-4 w-4" />
            <p className="text-sm">Solar radiation was estimated with atmospheric correction.</p>
          </div>
        ) : null}

        <div>
          <p className="mb-2 text-sm font-medium text-gray-800">Weather Snapshot</p>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <div className="rounded-lg border border-gray-100 p-3">
              <p className="mb-1 flex items-center gap-1 text-xs text-gray-500">
                <Thermometer className="h-3.5 w-3.5" />
                Temperature
              </p>
              <p className="text-sm font-medium text-gray-900">
                {Math.round(data.weather.tmax_c)} / {Math.round(data.weather.tmin_c)} C
              </p>
            </div>
            <div className="rounded-lg border border-gray-100 p-3">
              <p className="mb-1 flex items-center gap-1 text-xs text-gray-500">
                <Droplet className="h-3.5 w-3.5" />
                Humidity
              </p>
              <p className="text-sm font-medium text-gray-900">{Math.round(data.weather.rh2m_pct)}%</p>
            </div>
            <div className="rounded-lg border border-gray-100 p-3">
              <p className="mb-1 flex items-center gap-1 text-xs text-gray-500">
                <Wind className="h-3.5 w-3.5" />
                Wind
              </p>
              <p className="text-sm font-medium text-gray-900">{data.weather.ws2m_ms.toFixed(1)} m/s</p>
            </div>
            <div className="rounded-lg border border-gray-100 p-3">
              <p className="mb-1 flex items-center gap-1 text-xs text-gray-500">
                <Sun className="h-3.5 w-3.5" />
                Solar
              </p>
              <p className="text-sm font-medium text-gray-900">{Math.round(data.weather.rs_mj_m2_day)} MJ</p>
            </div>
          </div>
          <p className="mt-2 flex items-center gap-1 text-xs text-gray-500">
            <CloudSun className="h-3.5 w-3.5" />
            Data source: NASA weather feed
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

export default AdvisoryCard;
