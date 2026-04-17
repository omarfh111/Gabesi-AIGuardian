import { useState, useCallback } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../config';

export const usePollution = () => {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchReport = useCallback(async (params = {}) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/v1/pollution/report`, {
        farmer_id: params.farmer_id || 'demo_farmer',
        plot_id: params.plot_id || 'bahria_plot_a',
        language: params.language || 'en',
        window_days: params.window_days || 30,
      });
      setData(response.data);
    } catch (err) {
      console.error('Pollution Report Error:', err);
      setError('Failed to load pollution data.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { data, isLoading, error, fetchReport };
};
