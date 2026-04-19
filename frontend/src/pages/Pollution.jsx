import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { AlertTriangle, Download, ShieldAlert, Wind } from 'lucide-react';
import EventsTable from '../components/pollution/EventsTable';
import PollutionMap from '../components/pollution/PollutionMap';
import RiskBadge from '../components/pollution/RiskBadge';
import TrendChart from '../components/pollution/TrendChart';
import { Badge, Button, Card, CardContent, CardHeader, CardTitle } from '../components/ui';
import { API_BASE_URL } from '../config';
import { usePollution } from '../hooks/usePollution';

const Pollution = () => {
  const { t } = useTranslation();
  const { data, isLoading, error, fetchReport } = usePollution();
  const [isDownloading, setIsDownloading] = useState(false);

  useEffect(() => {
    fetchReport({
      farmer_id: 'demo_farmer',
      plot_id: 'bahria_plot_a',
      language: 'en',
      window_days: 30,
    });
  }, [fetchReport]);

  const handleDownload = async () => {
    if (!data) return;
    setIsDownloading(true);
    try {
      const resp = await axios.post(
        `${API_BASE_URL}/api/v1/pollution/pdf`,
        {
          farmer_id: 'demo_farmer',
          plot_id: 'bahria_plot_a',
          language: 'en',
          window_days: 30,
        },
        { responseType: 'blob' }
      );

      const blob = new Blob([resp.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `pollution_dossier_${data.report_id.slice(0, 8)}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download failed:', err);
      alert('Failed to generate PDF. Please try again.');
    } finally {
      setIsDownloading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-64px)] items-center justify-center bg-gray-50">
        <div className="text-sm text-gray-600">Calculating exposure risk...</div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex h-[calc(100vh-64px)] items-center justify-center bg-gray-50 p-6">
        <Card className="w-full max-w-md rounded-xl border-red-200 bg-red-50">
          <CardContent className="flex flex-col items-center gap-3 p-6 text-center">
            <ShieldAlert className="h-8 w-8 text-red-600" />
            <p className="text-sm font-medium text-red-700">{error || 'No data available'}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-64px)] bg-gradient-to-br from-slate-50 via-white to-sky-50 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <Card className="rounded-xl">
          <CardHeader className="flex-row items-start justify-between p-5">
            <div>
              <CardTitle className="flex items-center gap-2 text-lg font-semibold text-gray-900">
                <Wind className="h-5 w-5 text-gray-600" />
                {t('pollution.title')}
              </CardTitle>
              <p className="mt-1 text-sm text-gray-600">Exposure risk dossier for Gabes Oasis Plot A.</p>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="smoke">30-day window</Badge>
              <Button onClick={handleDownload} disabled={isDownloading}>
                <Download className="h-4 w-4" />
                {isDownloading ? 'Processing...' : t('pollution.downloadPdf')}
              </Button>
            </div>
          </CardHeader>
        </Card>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          <div className="space-y-6 lg:col-span-7">
            <Card className="h-[420px] overflow-hidden rounded-xl">
              <PollutionMap />
            </Card>
            <Card className="rounded-xl">
              <CardHeader className="p-5 pb-2">
                <CardTitle className="text-base font-medium text-gray-900">SO2 Concentration Timeline</CardTitle>
              </CardHeader>
              <CardContent className="p-5 pt-2">
                <TrendChart events={data.events} />
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6 lg:col-span-5">
            <RiskBadge level={data.insights.risk_level} />

            <div className="grid grid-cols-2 gap-4">
              <Card className="rounded-xl">
                <CardContent className="p-4">
                  <p className="text-xs text-gray-500">SO2 average</p>
                  <p className="mt-1 text-xl font-semibold text-gray-900">{Math.round(data.so2_stats?.mean || 0)} ug/m3</p>
                </CardContent>
              </Card>
              <Card className="rounded-xl">
                <CardContent className="p-4">
                  <p className="text-xs text-gray-500">NO2 average</p>
                  <p className="mt-1 text-xl font-semibold text-gray-900">{Math.round(data.no2_stats?.mean || 0)} ug/m3</p>
                </CardContent>
              </Card>
              <Card className="rounded-xl border-amber-200 bg-amber-50">
                <CardContent className="p-4">
                  <p className="text-xs text-amber-700">Elevated events</p>
                  <p className="mt-1 text-xl font-semibold text-amber-800">{data.total_elevated_days}</p>
                </CardContent>
              </Card>
              <Card className="rounded-xl border-red-200 bg-red-50">
                <CardContent className="p-4">
                  <p className="flex items-center gap-1 text-xs text-red-700">
                    <AlertTriangle className="h-3.5 w-3.5" />
                    Severe events
                  </p>
                  <p className="mt-1 text-xl font-semibold text-red-800">{data.total_severe_days}</p>
                </CardContent>
              </Card>
            </div>

            <Card className="rounded-xl">
              <CardHeader className="p-5 pb-2">
                <CardTitle className="text-base font-medium text-gray-900">Critical Event Log</CardTitle>
              </CardHeader>
              <CardContent className="p-5 pt-2">
                <EventsTable events={data.events?.slice(0, 5)} />
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Pollution;
