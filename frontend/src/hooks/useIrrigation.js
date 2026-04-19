import { useState } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../config';

export const useIrrigation = () => {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchAdvisory = async (params) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/v1/irrigation`, params);
      setData(response.data);
    } catch (err) {
      console.error('Irrigation API Error:', err);
      setError('Failed to fetch irrigation advisory. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return { data, isLoading, error, fetchAdvisory };
};
