import React from 'react';
import { useTranslation } from 'react-i18next';
import { CloudRain, Droplets, Satellite, Sprout } from 'lucide-react';
import AdvisoryCard from '../components/irrigation/AdvisoryCard';
import CropForm from '../components/irrigation/CropForm';
import { Badge, Card, CardContent, CardHeader, CardTitle } from '../components/ui';
import { useIrrigation } from '../hooks/useIrrigation';

const Irrigation = () => {
  const { t } = useTranslation();
  const { data, isLoading, error, fetchAdvisory } = useIrrigation();

  return (
    <div className="min-h-[calc(100vh-64px)] bg-gradient-to-br from-slate-50 via-white to-blue-50 p-6">
      <div className="mx-auto grid max-w-7xl grid-cols-1 gap-6 lg:grid-cols-12">
        <div className="space-y-6 lg:col-span-4">
          <Card className="rounded-xl">
            <CardHeader className="p-6 pb-3">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <CardTitle className="text-lg font-semibold text-gray-900">{t('irrigation.title')}</CardTitle>
                  <p className="mt-1 text-sm text-gray-600">
                    Water advisory based on crop stage and satellite weather data.
                  </p>
                </div>
                <Badge variant="water">
                  <Satellite className="mr-1 h-3.5 w-3.5" />
                  NASA
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="p-6 pt-0">
              <CropForm onSubmit={fetchAdvisory} isLoading={isLoading} />
            </CardContent>
          </Card>

          <Card className="rounded-xl">
            <CardContent className="grid grid-cols-2 gap-3 p-4">
              <div className="rounded-lg border border-gray-100 bg-gray-50 p-3">
                <p className="mb-1 flex items-center gap-1 text-xs text-gray-500">
                  <Sprout className="h-3.5 w-3.5" />
                  Method
                </p>
                <p className="text-sm font-medium text-gray-800">FAO-56 (ET0)</p>
              </div>
              <div className="rounded-lg border border-gray-100 bg-gray-50 p-3">
                <p className="mb-1 flex items-center gap-1 text-xs text-gray-500">
                  <CloudRain className="h-3.5 w-3.5" />
                  Forecast
                </p>
                <p className="text-sm font-medium text-gray-800">Daily update</p>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="lg:col-span-8">
          {error ? (
            <Card className="rounded-xl border-red-200 bg-red-50">
              <CardContent className="flex min-h-[420px] flex-col items-center justify-center p-8 text-center">
                <Droplets className="mb-3 h-8 w-8 text-red-600" />
                <p className="text-sm font-medium text-red-700">Calculation failed</p>
                <p className="mt-1 text-sm text-red-600">{error}</p>
              </CardContent>
            </Card>
          ) : data ? (
            <AdvisoryCard data={data} />
          ) : (
            <Card className="rounded-xl border-dashed border-gray-300">
              <CardContent className="flex min-h-[420px] flex-col items-center justify-center p-8 text-center">
                <Droplets className="mb-4 h-10 w-10 text-blue-500" />
                <p className="text-base font-medium text-gray-800">Ready for analysis</p>
                <p className="mt-1 max-w-sm text-sm text-gray-600">
                  Set crop parameters on the left to generate today&apos;s irrigation recommendation.
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default Irrigation;
