import { AlertTriangle, Droplets, Leaf, Siren, Wind } from 'lucide-react';

export const ISSUE_META = {
  smoke: {
    label: 'Smoke',
    color: '#6b7280',
    badgeVariant: 'smoke',
    Icon: Wind,
  },
  smell: {
    label: 'Smell',
    color: '#f59e0b',
    badgeVariant: 'smell',
    Icon: AlertTriangle,
  },
  dust: {
    label: 'Dust',
    color: '#92400e',
    badgeVariant: 'dust',
    Icon: Wind,
  },
  water: {
    label: 'Water',
    color: '#2563eb',
    badgeVariant: 'water',
    Icon: Droplets,
  },
  waste: {
    label: 'Waste',
    color: '#16a34a',
    badgeVariant: 'waste',
    Icon: Leaf,
  },
  symptoms: {
    label: 'Symptoms',
    color: '#dc2626',
    badgeVariant: 'symptoms',
    Icon: Siren,
  },
};

export const ISSUE_TYPES = ['smoke', 'smell', 'dust', 'water', 'waste', 'symptoms'];

export function getIssueMeta(type) {
  return ISSUE_META[type] || ISSUE_META.waste;
}
