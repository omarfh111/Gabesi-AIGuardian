import React from 'react';
import { useTranslation } from 'react-i18next';
import { Droplets, Wind, Thermometer, Droplet, AlertCircle, Sun, CloudRain } from 'lucide-react';

const AdvisoryCard = ({ data }) => {
  const { t } = useTranslation();
  if (!data) return null;

  return (
    <div className="glass-card p-8 flex flex-col h-full relative overflow-hidden group">
      {/* Subtle Background Icon */}
      <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
         <CloudRain className="w-32 h-32" />
      </div>

      <div className="text-center space-y-2 mb-8 relative z-10">
        <h3 className="text-[10px] font-black text-text-muted uppercase tracking-[0.3em]">Precision Irrigation Requirement</h3>
        <div className="text-6xl font-black text-accent flex items-baseline justify-center gap-2 tracking-tighter">
          {data.irrigation_depth_mm}
          <span className="text-xl font-bold uppercase text-text-muted tracking-widest">mm</span>
        </div>
        <p className="text-[9px] font-bold text-text-muted uppercase tracking-widest mt-2">Recommended daily water budget per m²</p>
      </div>

      <div className="glass bg-accent/5 border-accent/10 p-6 rounded-2xl text-sm font-medium leading-relaxed text-text-primary text-center mb-8 shadow-inner shadow-accent/5">
        {data.advisory_text}
      </div>

      <div className="grid grid-cols-2 gap-4 mb-8">
        <div className="glass p-5 rounded-2xl flex flex-col items-center justify-center group-hover:border-accent/30 transition-colors">
          <span className="text-[9px] font-black text-text-muted uppercase tracking-widest mb-2">ET₀ (Reference)</span>
          <span className="text-3xl font-black text-text-primary">
            {data.et0_mm_day} 
            <span className="text-[10px] text-text-muted ml-2">MM</span>
          </span>
        </div>
        <div className="glass p-5 rounded-2xl flex flex-col items-center justify-center group-hover:border-accent/30 transition-colors">
          <span className="text-[9px] font-black text-text-muted uppercase tracking-widest mb-2">Kc (Factor)</span>
          <span className="text-3xl font-black text-text-primary">{data.kc}</span>
        </div>
      </div>

      {data.rs_estimated && (
        <div className="flex items-center justify-center gap-3 text-[10px] font-black uppercase tracking-widest text-warning bg-warning/10 p-4 rounded-xl border border-warning/20 mb-8 animate-pulse">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>Solar radiation estimated (Atmospheric Correction Applied)</span>
        </div>
      )}

      <div className="border-t border-white/5 pt-8 mt-auto">
        <div className="flex items-center justify-between mb-6">
           <h4 className="text-[10px] font-black text-text-muted uppercase tracking-[0.2em]">Live Atmospheric Feed</h4>
           <span className="text-[9px] font-bold text-accent uppercase tracking-widest flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
              Satellite Sync Active
           </span>
        </div>
        
        <div className="grid grid-cols-4 gap-4">
          <div className="flex flex-col items-center justify-center glass py-4 rounded-xl group/stat">
            <Thermometer className="w-5 h-5 text-danger mb-2 group-hover/stat:scale-110 transition-transform" />
            <span className="text-[11px] font-black text-text-primary">{Math.round(data.weather.tmax_c)}°/{Math.round(data.weather.tmin_c)}°</span>
            <span className="text-[8px] font-bold text-text-muted uppercase mt-1">Temp</span>
          </div>
          <div className="flex flex-col items-center justify-center glass py-4 rounded-xl group/stat">
            <Droplet className="w-5 h-5 text-accent mb-2 group-hover/stat:scale-110 transition-transform" />
            <span className="text-[11px] font-black text-text-primary">{Math.round(data.weather.rh2m_pct)}%</span>
            <span className="text-[8px] font-bold text-text-muted uppercase mt-1">Humid</span>
          </div>
          <div className="flex flex-col items-center justify-center glass py-4 rounded-xl group/stat">
            <Wind className="w-5 h-5 text-purple mb-2 group-hover/stat:scale-110 transition-transform" />
            <span className="text-[11px] font-black text-text-primary">{data.weather.ws2m_ms.toFixed(1)} <span className="text-[8px] text-text-muted">m/s</span></span>
            <span className="text-[8px] font-bold text-text-muted uppercase mt-1">Wind</span>
          </div>
          <div className="flex flex-col items-center justify-center glass py-4 rounded-xl group/stat">
            <Sun className="w-5 h-5 text-yellow-500 mb-2 group-hover/stat:scale-110 transition-transform" />
            <span className="text-[11px] font-black text-text-primary">{Math.round(data.weather.rs_mj_m2_day)} <span className="text-[8px] text-text-muted">MJ</span></span>
            <span className="text-[8px] font-bold text-text-muted uppercase mt-1">Solar</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdvisoryCard;
