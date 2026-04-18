import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface Report {
  id: string;
  rounded_lat: number;
  rounded_lng: number;
  issue_type: string;
  severity: string;
  description?: string;
  symptom_tags?: string[];
  created_at: string;
}

export interface ReportDetails extends Report {
  ai_summary?: string;
  similar_count: number;
  confidence_score: number;
  risk_level: string;
}

export const fetchReports = async (filters: any) => {
  const { data } = await axios.get(`${API_URL}/reports`, { params: filters });
  return data;
};

export const fetchReportDetails = async (id: string) => {
  const { data } = await axios.get(`${API_URL}/reports/${id}`);
  return data;
};

export const submitReport = async (payload: any) => {
  const { data } = await axios.post(`${API_URL}/reports`, payload);
  return data;
};
