import { cn } from './utils';

export function Card({ className = '', children, ...props }) {
  return (
    <section
      className={cn('rounded-xl border border-gray-200 bg-white shadow-sm', className)}
      {...props}
    >
      {children}
    </section>
  );
}

export function CardHeader({ className = '', children, ...props }) {
  return (
    <header className={cn('flex items-start justify-between gap-3 p-4 pb-3', className)} {...props}>
      {children}
    </header>
  );
}

export function CardTitle({ className = '', children, ...props }) {
  return (
    <h3 className={cn('text-lg font-semibold text-gray-900', className)} {...props}>
      {children}
    </h3>
  );
}

export function CardDescription({ className = '', children, ...props }) {
  return (
    <p className={cn('text-sm text-gray-600', className)} {...props}>
      {children}
    </p>
  );
}

export function CardContent({ className = '', children, ...props }) {
  return (
    <div className={cn('p-4 pt-0', className)} {...props}>
      {children}
    </div>
  );
}

export function CardFooter({ className = '', children, ...props }) {
  return (
    <footer className={cn('flex items-center justify-end gap-2 border-t border-gray-100 p-4', className)} {...props}>
      {children}
    </footer>
  );
}
