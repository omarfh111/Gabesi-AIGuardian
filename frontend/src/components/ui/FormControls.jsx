import { cn } from './utils';

const BASE_CONTROL_STYLES =
  'w-full rounded-lg border border-gray-200 bg-white px-3 py-2.5 text-sm text-gray-800 shadow-sm transition-colors duration-200 placeholder:text-gray-400 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 disabled:cursor-not-allowed disabled:bg-gray-100';

export function FormField({ label, meta, htmlFor, className = '', children }) {
  return (
    <div className={cn('space-y-1.5', className)}>
      {label ? (
        <label htmlFor={htmlFor} className="block text-sm font-medium text-gray-700">
          {label}
        </label>
      ) : null}
      {children}
      {meta ? <p className="text-xs text-gray-500">{meta}</p> : null}
    </div>
  );
}

export function Input({ className = '', ...props }) {
  return <input className={cn(BASE_CONTROL_STYLES, className)} {...props} />;
}

export function Select({ className = '', children, ...props }) {
  return (
    <select className={cn(BASE_CONTROL_STYLES, className)} {...props}>
      {children}
    </select>
  );
}

export function Textarea({ className = '', rows = 4, ...props }) {
  return <textarea rows={rows} className={cn(BASE_CONTROL_STYLES, 'resize-none', className)} {...props} />;
}
