import { cn } from './utils';

const BADGE_STYLES = {
  neutral: 'bg-gray-100 text-gray-700 border-gray-200',
  smoke: 'bg-gray-100 text-gray-700 border-gray-300',
  smell: 'bg-amber-100 text-amber-800 border-amber-200',
  water: 'bg-blue-100 text-blue-700 border-blue-200',
  waste: 'bg-green-100 text-green-700 border-green-200',
  dust: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  symptoms: 'bg-red-100 text-red-700 border-red-200',
  low: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  high: 'bg-red-100 text-red-700 border-red-200',
};

export default function Badge({ variant = 'neutral', className = '', children, ...props }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-lg border px-2.5 py-1 text-xs font-medium',
        BADGE_STYLES[variant] || BADGE_STYLES.neutral,
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}
