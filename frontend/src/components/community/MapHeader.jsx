import { Activity, LocateFixed } from 'lucide-react';
import { Card, CardContent } from '../ui';

export default function MapHeader({ reportCount, isModalOpen, isRefreshing }) {
  return (
    <div className="pointer-events-none absolute left-4 right-4 top-4 z-10">
      <div className="mx-auto flex max-w-[1400px] items-start justify-between gap-4">
        <Card className="pointer-events-auto w-[380px] rounded-xl bg-white/95 backdrop-blur">
          <CardContent className="p-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs text-gray-500">Community Intelligence</p>
                <h1 className="text-lg font-semibold text-gray-900">Gabes Environment Map</h1>
                <p className="mt-1 text-sm text-gray-600">
                  Click the map to submit an anonymous report. Data refreshes every 30 seconds.
                </p>
              </div>
              <div className="rounded-lg bg-sky-50 p-2 text-sky-700">
                <Activity className="h-5 w-5" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="pointer-events-auto rounded-xl bg-white/95 backdrop-blur">
          <CardContent className="flex items-center gap-2 p-3">
            <LocateFixed className="h-4 w-4 text-sky-700" />
            <p className="text-sm text-gray-700">
              <span className="font-semibold text-gray-900">{reportCount}</span> reports visible
              {isModalOpen ? ' - submitting new report' : ''}
              {isRefreshing ? ' - updating...' : ''}
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
