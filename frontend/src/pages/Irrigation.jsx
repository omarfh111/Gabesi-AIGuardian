import React from 'react';
import { useTranslation } from 'react-i18next';
import { useIrrigation } from '../hooks/useIrrigation';
import CropForm from '../components/irrigation/CropForm';
import AdvisoryCard from '../components/irrigation/AdvisoryCard';
import { Droplets, CloudRain } from 'lucide-react';

const Irrigation = () => {
  const { t } = useTranslation();
  const { data, isLoading, error, fetchAdvisory } = useIrrigation();

  return (
    <div className="p-4 md:p-8 max-w-5xl mx-auto space-y-6 lg:h-[calc(100vh-64px)] flex flex-col justify-center">
      <div className="flex flex-col items-center gap-3 justify-center mb-8 text-center bg-white p-8 rounded-3xl shadow-sm border border-gray-100">
        <div className="bg-primary/10 p-4 rounded-2xl text-primary mb-2 shadow-inner">
          <Droplets className="w-10 h-10" />
        </div>
        <div>
          <h1 className="text-3xl font-black text-gray-800 tracking-tight mb-2 flex items-center justify-center gap-2">
              {t('irrigation.title')}
          </h1>
          <p className="text-gray-500 font-medium">Calculate precise daily watering needs using NASA satellite data</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-stretch h-full lg:h-auto min-h-[500px]">
        <div className="h-full flex flex-col">
            <h2 className="text-sm font-bold text-gray-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                1. Configure Crop
            </h2>
            <div className="flex-1 bg-white rounded-3xl p-2 shadow-sm border border-gray-100">
                <CropForm onSubmit={fetchAdvisory} isLoading={isLoading} />
            </div>
        </div>
        
        <div className="h-full flex flex-col">
            <h2 className="text-sm font-bold text-gray-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                2. Advisory Result
            </h2>
          {error ? (
            <div className="bg-red-50 text-red-600 p-8 rounded-3xl border border-red-100 h-full flex flex-col items-center justify-center text-center font-medium shadow-sm">
                <CloudRain className="w-12 h-12 mb-4 opacity-50" />
              {error}
            </div>
          ) : data ? (
            <div className="flex-1">
                <AdvisoryCard data={data} />
            </div>
          ) : (
            <div className="bg-white p-8 rounded-3xl border border-gray-100 border-dashed h-full flex flex-col items-center justify-center text-gray-400 text-center space-y-4 min-h-[400px]">
              <div className="bg-gray-50 p-6 rounded-full border border-gray-100 mb-2">
                  <Droplets className="w-16 h-16 opacity-20 text-primary" />
              </div>
              <p className="text-sm font-medium leading-relaxed max-w-[200px]">Submit the form on the left to generate your daily irrigation advisory.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Irrigation;
