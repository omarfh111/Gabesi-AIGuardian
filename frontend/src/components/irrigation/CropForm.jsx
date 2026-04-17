import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';

const CropForm = ({ onSubmit, isLoading }) => {
  const { t } = useTranslation();
  const [cropType, setCropType] = useState('date_palm');
  const [growthStage, setGrowthStage] = useState('mid');
  const [language, setLanguage] = useState('en');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({ crop_type: cropType, growth_stage: growthStage, language });
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 space-y-4">
      <div>
        <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Crop Type</label>
        <select 
          value={cropType} 
          onChange={(e) => setCropType(e.target.value)}
          className="w-full border rounded-xl p-3 bg-gray-50 hover:bg-white focus:ring-2 focus:ring-primary focus:bg-white outline-none transition-all cursor-pointer font-medium text-gray-800"
        >
          <option value="date_palm">Date Palm (Deglet Nour)</option>
          <option value="pomegranate">Pomegranate</option>
          <option value="fig">Fig</option>
          <option value="olive">Olive</option>
          <option value="vegetables">Vegetables / Ground Crops</option>
        </select>
      </div>

      <div>
        <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Growth Stage</label>
        <select 
          value={growthStage} 
          onChange={(e) => setGrowthStage(e.target.value)}
          className="w-full border rounded-xl p-3 bg-gray-50 hover:bg-white focus:ring-2 focus:ring-primary focus:bg-white outline-none transition-all cursor-pointer font-medium text-gray-800"
        >
          <option value="initial">Initial (Planting/Early Growth)</option>
          <option value="mid">Mid (Flowering/Fruiting)</option>
          <option value="end">End (Harvest/Dormancy)</option>
        </select>
      </div>

      <div>
        <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Advisory Language</label>
        <select 
          value={language} 
          onChange={(e) => setLanguage(e.target.value)}
          className="w-full border rounded-xl p-3 bg-gray-50 hover:bg-white focus:ring-2 focus:ring-primary focus:bg-white outline-none transition-all cursor-pointer font-medium text-gray-800"
        >
          <option value="en">English</option>
          <option value="fr">French</option>
          <option value="ar">Arabic (العربية)</option>
        </select>
      </div>

      <button 
        type="submit" 
        disabled={isLoading}
        className="w-full bg-primary text-white py-3.5 rounded-xl font-bold hover:bg-opacity-90 transition-opacity disabled:opacity-50 mt-4 shadow-sm"
      >
        {isLoading ? 'Calculating...' : "Get Today's Advisory"}
      </button>
    </form>
  );
};

export default CropForm;
