import { create } from 'zustand';
import { Report } from './api';

interface AppState {
  reports: Report[];
  setReports: (reports: Report[]) => void;
  selectedLocation: { lat: number; lng: number } | null;
  setSelectedLocation: (loc: { lat: number; lng: number } | null) => void;
  isModalOpen: boolean;
  setIsModalOpen: (isOpen: boolean) => void;
  filters: {
    issueType: string | null;
    severity: string | null;
  };
  setFilter: (key: 'issueType' | 'severity', value: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  reports: [],
  setReports: (reports) => set({ reports }),
  selectedLocation: null,
  setSelectedLocation: (loc) => set({ selectedLocation: loc, isModalOpen: !!loc }),
  isModalOpen: false,
  setIsModalOpen: (isOpen) => set({ isModalOpen: isOpen }),
  filters: {
    issueType: null,
    severity: null,
  },
  setFilter: (key, value) => 
    set((state) => ({ filters: { ...state.filters, [key]: value } })),
}));
