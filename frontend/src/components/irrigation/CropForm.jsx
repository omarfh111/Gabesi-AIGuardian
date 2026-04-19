import React, { useState } from 'react';
import { Loader2 } from 'lucide-react';
import { Button, FormField, Select } from '../ui';

const CropForm = ({ onSubmit, isLoading }) => {
  const [cropType, setCropType] = useState('date_palm');
  const [growthStage, setGrowthStage] = useState('mid');
  const [language, setLanguage] = useState('en');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({ crop_type: cropType, growth_stage: growthStage, language });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <FormField label="Crop Type" htmlFor="cropType">
        <Select id="cropType" value={cropType} onChange={(e) => setCropType(e.target.value)}>
          <option value="date_palm">Date Palm (Deglet Nour)</option>
          <option value="pomegranate">Pomegranate</option>
          <option value="fig">Fig</option>
          <option value="olive">Olive</option>
          <option value="vegetables">Vegetables / Ground Crops</option>
        </Select>
      </FormField>

      <FormField label="Growth Stage" htmlFor="growthStage">
        <Select id="growthStage" value={growthStage} onChange={(e) => setGrowthStage(e.target.value)}>
          <option value="initial">Initial (Planting/Early Growth)</option>
          <option value="mid">Mid (Flowering/Fruiting)</option>
          <option value="end">End (Harvest/Dormancy)</option>
        </Select>
      </FormField>

      <FormField label="Output Language" htmlFor="language">
        <Select id="language" value={language} onChange={(e) => setLanguage(e.target.value)}>
          <option value="en">English</option>
          <option value="fr">French</option>
          <option value="ar">Arabic</option>
        </Select>
      </FormField>

      <Button type="submit" className="w-full" loading={isLoading}>
        {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
        {isLoading ? 'Processing NASA Data...' : 'Generate Advisory'}
      </Button>
      <p className="text-xs text-gray-500">
        Uses FAO-56 Penman-Monteith method with NASA weather inputs.
      </p>
    </form>
  );
};

export default CropForm;
