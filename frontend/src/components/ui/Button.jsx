import React from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from './utils';

const VARIANT_STYLES = {
  primary: 'bg-sky-600 text-white hover:bg-sky-500 shadow-sm',
  secondary: 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50 shadow-sm',
};

const SIZE_STYLES = {
  sm: 'h-9 px-3 text-sm',
  md: 'h-10 px-4 text-sm',
  lg: 'h-11 px-5 text-sm',
};

const DISABLED_STYLES = 'cursor-not-allowed opacity-50 hover:bg-inherit';

const Button = React.forwardRef(function Button(
  { type = 'button', variant = 'primary', size = 'md', className = '', disabled = false, loading = false, children, ...props },
  ref
) {
  const isDisabled = disabled || loading;

  return (
    <button
      ref={ref}
      type={type}
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400 focus-visible:ring-offset-2',
        VARIANT_STYLES[variant] || VARIANT_STYLES.primary,
        SIZE_STYLES[size] || SIZE_STYLES.md,
        isDisabled ? DISABLED_STYLES : '',
        className
      )}
      disabled={isDisabled}
      {...props}
    >
      {loading && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
      {children}
    </button>
  );
});

export default Button;
