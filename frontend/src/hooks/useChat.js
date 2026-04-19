import { useState } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { API_BASE_URL } from '../config';

export const useChat = () => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const { i18n } = useTranslation();

  const sendMessage = async (text) => {
    if (!text.trim()) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/v1/chat`, {
        message: text,
        farmer_id: 'demo_farmer',
        plot_id: 'bahria_plot_a',
        language: i18n.language || 'en',
        crop_type: 'date_palm',
        growth_stage: 'mid',
      });

      const aiMessage = {
        id: Date.now() + 1,
        role: 'ai',
        ...response.data, // Contains intent, response (payload), agent_used, timestamp
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (err) {
      console.error('Chat API Error:', err);
      setError('Unable to process your request. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return {
    messages,
    isLoading,
    error,
    sendMessage,
  };
};
