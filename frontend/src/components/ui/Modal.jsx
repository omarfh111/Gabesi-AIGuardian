import { useEffect } from 'react';
import { X } from 'lucide-react';
import { cn } from './utils';

const SIZE_STYLES = {
  sm: 'max-w-md',
  md: 'max-w-xl',
  lg: 'max-w-2xl',
};

export default function Modal({
  isOpen,
  onClose,
  title,
  description,
  icon,
  size = 'sm',
  children,
  footer,
  className = '',
  closeOnBackdrop = true,
}) {
  useEffect(() => {
    if (!isOpen) return undefined;

    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    const onKeyDown = (event) => {
      if (event.key === 'Escape') onClose?.();
    };
    window.addEventListener('keydown', onKeyDown);

    return () => {
      document.body.style.overflow = originalOverflow;
      window.removeEventListener('keydown', onKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-[2000] flex items-center justify-center bg-black/45 p-4 backdrop-blur-sm"
      onClick={closeOnBackdrop ? onClose : undefined}
      role="presentation"
    >
      <div
        className={cn(
          'w-full rounded-xl border border-gray-200 bg-white shadow-md',
          SIZE_STYLES[size] || SIZE_STYLES.sm,
          className
        )}
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        <header className="flex items-start justify-between gap-4 border-b border-gray-100 p-6">
          <div className="flex min-w-0 items-start gap-3">
            {icon ? (
              <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gray-100 text-gray-700">
                {icon}
              </div>
            ) : null}
            <div className="min-w-0">
              {title ? <h2 className="text-lg font-semibold text-gray-900">{title}</h2> : null}
              {description ? <p className="mt-1 text-sm text-gray-600">{description}</p> : null}
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700"
            aria-label="Close modal"
          >
            <X className="h-4 w-4" />
          </button>
        </header>

        <div className="p-6">{children}</div>
        {footer ? <footer className="border-t border-gray-100 p-6 pt-4">{footer}</footer> : null}
      </div>
    </div>
  );
}
