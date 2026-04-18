import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ChevronDown, Loader2 } from 'lucide-react';

const CropForm = ({ onSubmit, isLoading }) => {
  const { t } = useTranslation();
  const [cropType, setCropType] = useState('date_palm');
  const [growthStage, setGrowthStage] = useState('mid');
  const [language, setLanguage] = useState('en');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({ crop_type: cropType, growth_stage: growthStage, language });
  };

  const selectClasses = "w-full appearance-none bg-primary/40 border border-white/10 rounded-xl p-3.5 text-sm text-text-primary font-bold focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/30 transition-all cursor-pointer";

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-4">
        <div className="relative group">
          <label className="block text-[10px] font-black text-text-muted uppercase tracking-[0.2em] mb-2 group-focus-within:text-accent transition-colors">
            Crop Taxonomy
          </label>
          <div className="relative">
            <select 
              value={cropType} 
              onChange={(e) => setCropType(e.target.value)}
              className={selectClasses}
            >
              <option value="date_palm">Date Palm (Deglet Nour)</option>
              <option value="pomegranate">Pomegranate</option>
              <option value="fig">Fig</option>
              <option value="olive">Olive</option>
              <option value="vegetables">Vegetables / Ground Crops</option>
            </select>
            <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted pointer-events-none group-focus-within:text-accent transition-colors" />
          </div>
        </div>

        <div className="relative group">
          <label className="block text-[10px] font-black text-text-muted uppercase tracking-[0.2em] mb-2 group-focus-within:text-accent transition-colors">
            Biological Phase
          </label>
          <div className="relative">
            <select 
              value={growthStage} 
              onChange={(e) => setGrowthStage(e.target.value)}
              className={selectClasses}
            >
              <option value="initial">Initial (Planting/Early Growth)</option>
              <option value="mid">Mid (Flowering/Fruiting)</option>
              <option value="end">End (Harvest/Dormancy)</option>
            </select>
            <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted pointer-events-none group-focus-within:text-accent transition-colors" />
          </div>
        </div>

        <div className="relative group">
          <label className="block text-[10px] font-black text-text-muted uppercase tracking-[0.2em] mb-2 group-focus-within:text-accent transition-colors">
            Output Language
          </label>
          <div className="relative">
            <select 
              value={language} 
              onChange={(e) => setLanguage(e.target.value)}
              className={selectClasses}
            >
              <option value="en">English (Professional)</option>
              <option value="fr">French (Français)</option>
              <option value="ar">Arabic (العربية)</option>
            </select>
            <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted pointer-events-none group-focus-within:text-accent transition-colors" />
          </div>
        </div>
      </div>

      <button 
        type="submit" 
        disabled={isLoading}
        className="group relative w-full overflow-hidden rounded-xl bg-accent py-4 text-[11px] font-black uppercase tracking-[0.2em] text-primary transition-all hover:scale-[1.02] active:scale-95 disabled:opacity-50 disabled:grayscale cursor-pointer shadow-lg shadow-accent/20"
      >
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
        <div className="flex items-center justify-center gap-2">
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Processing NASA Data...
            </>
          ) : (
            "Execute Advisory Engine"
          )}
        </div>
      </button>
      
      <p className="text-[9px] text-center text-text-muted font-bold uppercase tracking-widest leading-relaxed">
        * Calculation utilizes FAO-56 Penman-Monteith methodology for optimal water efficiency.
      </p>
    </form>
  );
};

export default CropForm;
