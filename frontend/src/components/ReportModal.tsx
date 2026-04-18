import React, { useState } from 'react';
import { useAppStore } from '../store';
import { submitReport } from '../api';
import { X, Loader2 } from 'lucide-react';

export default function ReportModal() {
  const isModalOpen = useAppStore(state => state.isModalOpen);
  const setIsModalOpen = useAppStore(state => state.setIsModalOpen);
  const selectedLocation = useAppStore(state => state.selectedLocation);
  
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    issue_type: 'waste',
    severity: 'medium',
    description: '',
    symptoms: ''
  });

  if (!isModalOpen || !selectedLocation) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const payload = {
        lat: selectedLocation.lat,
        lng: selectedLocation.lng,
        issue_type: formData.issue_type,
        severity: formData.severity,
        description: formData.description,
        symptom_tags: formData.symptoms ? formData.symptoms.split(',').map(s => s.trim()) : []
      };
      
      await submitReport(payload);
      setIsModalOpen(false);
      // Ideally we refresh the reports here, or the App.tsx loop will catch it
      window.location.reload(); 
    } catch (err) {
      console.error(err);
      alert('Failed to submit report. Ensure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[2000] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200">
        <div className="flex justify-between items-center p-5 border-b border-gray-100 bg-gray-50/50">
          <h2 className="text-xl font-semibold text-gray-800">Report Environmental Issue</h2>
          <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-gray-600 transition-colors">
            <X size={20} />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Issue Type</label>
            <select 
              value={formData.issue_type}
              onChange={e => setFormData({...formData, issue_type: e.target.value})}
              className="w-full rounded-lg border-gray-300 shadow-sm focus:border-gabes-500 focus:ring-gabes-500 border p-2"
            >
              <option value="smoke">Smoke / Air Pollution</option>
              <option value="smell">Strong Chemical Smell</option>
              <option value="dust">Chemical Dust</option>
              <option value="water">Water Contamination</option>
              <option value="waste">Industrial Waste</option>
              <option value="symptoms">Health Symptoms</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Severity</label>
            <div className="flex gap-4 mt-2">
              {['low', 'medium', 'high'].map(sev => (
                <label key={sev} className="flex items-center">
                  <input type="radio" name="severity" value={sev}
                    checked={formData.severity === sev}
                    onChange={e => setFormData({...formData, severity: e.target.value})}
                    className="text-gabes-500 focus:ring-gabes-500"
                  />
                  <span className="ml-2 text-sm text-gray-600 capitalize">{sev}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description (Optional)</label>
            <textarea 
              rows={3} 
              value={formData.description}
              onChange={e => setFormData({...formData, description: e.target.value})}
              className="w-full rounded-lg border border-gray-300 p-2 shadow-sm focus:border-gabes-500 focus:ring-gabes-500"
              placeholder="What are you experiencing?"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Symptoms (Comma separated, Optional)</label>
            <input 
              type="text" 
              value={formData.symptoms}
              onChange={e => setFormData({...formData, symptoms: e.target.value})}
              className="w-full rounded-lg border border-gray-300 p-2 shadow-sm focus:border-gabes-500 focus:ring-gabes-500"
              placeholder="e.g. coughing, headache, nausea"
            />
          </div>

          <div className="pt-4">
            <button 
              type="submit" 
              disabled={loading}
              className="w-full bg-gabes-500 text-white rounded-lg py-2.5 font-medium hover:bg-gabes-600 transition-colors shadow-md flex justify-center items-center gap-2 disabled:opacity-70"
            >
              {loading && <Loader2 size={18} className="animate-spin" />}
              {loading ? 'Submitting...' : 'Submit Anonymous Report'}
            </button>
            <p className="text-center text-xs text-gray-400 mt-3">
              Your location is slightly randomized to protect your privacy.
            </p>
          </div>
        </form>
      </div>
    </div>
  );
}
