'use client';

import { InputHTMLAttributes, forwardRef, useId } from 'react';
import { cn } from '@/lib/utils';
import { AlertCircle } from 'lucide-react';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  helperText?: string;
  leadingIcon?: React.ReactNode;
  trailingIcon?: React.ReactNode;
  required?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      helperText,
      leadingIcon,
      trailingIcon,
      required,
      id,
      className,
      disabled,
      'aria-describedby': ariaDescribedBy,
      ...props
    },
    ref
  ) => {
    const generatedId = useId();
    const inputId = id || generatedId;
    const errorId = error ? `${inputId}-error` : undefined;
    const helperId = helperText && !error ? `${inputId}-helper` : undefined;

    return (
      <div className="relative w-full">
        <label
          htmlFor={inputId}
          className={cn(
            'block text-label-large text-on-surface mb-1.5',
            required && 'after:content-["*"] after:ml-0.5 after:text-error'
          )}
        >
          {label}
        </label>
        <div className="relative">
          {leadingIcon && (
            <div
              className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-on-surface-variant"
              aria-hidden="true"
            >
              {leadingIcon}
            </div>
          )}
          <input
            ref={ref}
            id={inputId}
            className={cn(
              'w-full px-4 py-2.5 rounded-md border transition-colors duration-fast ease-out-quick',
              'bg-surface text-on-surface placeholder:text-on-surface-disabled',
              'border-outline',
              'hover:border-outline-strong',
              'focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary',
              'disabled:bg-surface-container-low disabled:text-on-surface-disabled disabled:cursor-not-allowed',
              leadingIcon && 'pl-10',
              trailingIcon && 'pr-10',
              error && 'border-error focus:ring-error focus:border-error',
              className
            )}
            aria-invalid={error ? 'true' : 'false'}
            aria-describedby={cn(errorId, helperId, ariaDescribedBy)}
            aria-required={required}
            disabled={disabled}
            {...props}
          />
          {trailingIcon && (
            <div
              className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none text-on-surface-variant"
              aria-hidden="true"
            >
              {trailingIcon}
            </div>
          )}
        </div>
        {error && (
          <p
            id={errorId}
            className="mt-1.5 text-body-small text-error flex items-center gap-1"
            role="alert"
            aria-live="assertive"
          >
            <AlertCircle className="w-4 h-4 flex-shrink-0" aria-hidden="true" />
            {error}
          </p>
        )}
        {helperText && !error && (
          <p
            id={helperId}
            className="mt-1.5 text-body-small text-on-surface-variant"
            aria-live="polite"
          >
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';