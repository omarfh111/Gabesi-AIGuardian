import React from 'react';
import { useTranslation } from 'react-i18next';
import { useIrrigation } from '../hooks/useIrrigation';
import CropForm from '../components/irrigation/CropForm';
import AdvisoryCard from '../components/irrigation/AdvisoryCard';
import { Droplets, CloudRain, Sprout, Database, Satellite } from 'lucide-react';

const Irrigation = () => {
  const { t } = useTranslation();
  const { data, isLoading, error, fetchAdvisory } = useIrrigation();

  return (
    <div className="bg-primary min-h-[calc(100vh-64px)] overflow-hidden relative">
      {/* Background Glow */}
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-accent/5 rounded-full blur-[150px] -z-10" />
      
      <div className="max-w-7xl mx-auto p-6 lg:p-12">
        <div className="flex flex-col lg:flex-row gap-12 items-center lg:items-start">
          
          {/* Left: Info & Form */}
          <div className="lg:w-1/3 space-y-8">
            <div className="space-y-4">
              <div className="inline-flex items-center gap-2 px-3 py-1 glass border-accent/30 rounded-full text-[10px] font-black uppercase tracking-widest text-accent">
                <Satellite className="w-3 h-3" />
                NASA POWER API Integration
              </div>
              <h1 className="text-4xl font-black text-text-primary tracking-tighter uppercase leading-none">
                {t('irrigation.title')}
              </h1>
              <p className="text-text-secondary font-medium leading-relaxed">
                Precision water management using FAO-56 Penman-Monteith methodology and real-time satellite weather data.
              </p>
            </div>

            <div className="glass-card p-6 border-accent/20">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center text-accent">
                  <Sprout className="w-5 h-5" />
                </div>
                <h2 className="text-xs font-black text-text-primary uppercase tracking-[0.2em]">Crop Configuration</h2>
              </div>
              <CropForm onSubmit={fetchAdvisory} isLoading={isLoading} />
            </div>

            <div className="grid grid-cols-2 gap-4">
               <div className="glass p-4 rounded-2xl flex flex-col gap-1">
                  <Database className="w-4 h-4 text-purple" />
                  <span className="text-[10px] font-black text-text-muted uppercase">Data Source</span>
                  <span className="text-xs font-bold text-text-primary">FAO-56 DB</span>
               </div>
               <div className="glass p-4 rounded-2xl flex flex-col gap-1">
                  <Droplets className="w-4 h-4 text-accent" />
                  <span className="text-[10px] font-black text-text-muted uppercase">Method</span>
                  <span className="text-xs font-bold text-text-primary">ETo Daily</span>
               </div>
            </div>
          </div>

          {/* Right: Result Area */}
          <div className="lg:w-2/3 w-full h-full min-h-[600px] flex flex-col">
            <div className="flex items-center justify-between mb-6">
               <h2 className="text-[10px] font-black text-text-muted uppercase tracking-[0.2em] flex items-center gap-3">
                  <CloudRain className="w-4 h-4 text-accent" />
                  Optimization Engine Output
               </h2>
               {isLoading && <span className="text-[10px] font-black text-accent animate-pulse uppercase tracking-widest">Processing Satellite Data...</span>}
            </div>

            {error ? (
              <div className="flex-1 glass-card border-danger/30 p-12 flex flex-col items-center justify-center text-center group">
                <div className="w-20 h-20 bg-danger/10 rounded-full flex items-center justify-center text-danger mb-6 group-hover:scale-110 transition-transform">
                  <CloudRain className="w-10 h-10" />
                </div>
                <span className="text-sm font-black text-danger uppercase tracking-widest mb-2">Calculation Failed</span>
                <p className="text-text-secondary text-sm max-w-xs mx-auto">{error}</p>
              </div>
            ) : data ? (
              <div className="flex-1 animate-in fade-in zoom-in-95 duration-500">
                <AdvisoryCard data={data} />
              </div>
            ) : (
              <div className="flex-1 glass-card border-dashed border-border flex flex-col items-center justify-center text-center p-12 group">
                <div className="w-24 h-24 bg-accent/5 rounded-full flex items-center justify-center text-accent mb-8 group-hover:bg-accent/10 transition-colors">
                  <Droplets className="w-12 h-12 opacity-30" />
                </div>
                <h3 className="text-lg font-black text-text-primary uppercase tracking-tighter mb-2">Ready for Analysis</h3>
                <p className="text-text-secondary text-sm max-w-xs mx-auto">
                  Configure your crop parameters on the left and trigger the AI advisory engine to calculate today's requirements.
                </p>
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
};

export default Irrigation;
