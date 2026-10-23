'use client';

import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

export type SpinnerSize = 'sm' | 'md' | 'lg';

export interface SpinnerProps extends HTMLAttributes<HTMLDivElement> {
  size?: SpinnerSize;
  label?: string;
}

const sizeStyles: Record<SpinnerSize, string> = {
  sm: 'w-4 h-4 border-2',
  md: 'w-6 h-6 border-2',
  lg: 'w-8 h-8 border-3',
};

export const Spinner = forwardRef<HTMLDivElement, SpinnerProps>(
  ({ size = 'md', label, className, 'aria-label': ariaLabel, ...props }, ref) => (
    <div
      ref={ref}
      role="status"
      aria-label={ariaLabel || label || 'Loading'}
      aria-live="polite"
      className={cn(
        'inline-flex',
        'animate-spin',
        'rounded-full',
        'border-primary',
        'border-t-transparent',
        sizeStyles[size],
        className
      )}
      {...props}
    >
      <span className="sr-only">{label || 'Loading'}</span>
    </div>
  )
);

Spinner.displayName = 'Spinner';

/* ---------------------------------------------------------------------------
   Inline Spinner — For button loading states
   --------------------------------------------------------------------------- */

export interface InlineSpinnerProps extends HTMLAttributes<HTMLSpanElement> {
  size?: 'sm' | 'md';
}

export const InlineSpinner = forwardRef<HTMLSpanElement, InlineSpinnerProps>(
  ({ size = 'md', className, ...props }, ref) => (
    <span
      ref={ref}
      role="status"
      aria-label="Loading"
      aria-live="polite"
      className={cn(
        'inline-flex',
        'animate-spin',
        'rounded-full',
        'border-primary',
        'border-t-transparent',
        size === 'sm' ? 'w-4 h-4 border-2' : 'w-5 h-5 border-2',
        className
      )}
      {...props}
    >
      <span className="sr-only">Loading</span>
    </span>
  )
);

InlineSpinner.displayName = 'InlineSpinner';

/* ---------------------------------------------------------------------------
   Skeleton — For content placeholders
   --------------------------------------------------------------------------- */

export interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
}

export function Skeleton({
  variant = 'text',
  width,
  height,
  className,
  ...props
}: SkeletonProps) {
  const baseStyles = 'animate-pulse bg-surface-container-high rounded';

  const variantStyles = {
    text: 'h-4 rounded-full',
    circular: 'rounded-full',
    rectangular: 'rounded-md',
  }[variant];

  return (
    <div
      className={cn(baseStyles, variantStyles, className)}
      style={{ width, height }}
      aria-hidden="true"
      {...props}
    />
  );
}

/* ---------------------------------------------------------------------------
   Skeleton Variants — Pre-configured skeletons for common patterns
   --------------------------------------------------------------------------- */

export function CardSkeleton() {
  return (
    <div className="space-y-4 p-4 bg-surface-container rounded-xl shadow-elev-1">
      <Skeleton variant="rectangular" className="h-6 w-3/4" />
      <Skeleton variant="text" className="h-4 w-full" />
      <Skeleton variant="text" className="h-4 w-5/6" />
      <Skeleton variant="text" className="h-4 w-2/3" />
    </div>
  );
}

export interface ListSkeletonProps {
  count?: number;
}

export function ListSkeleton({ count = 3 }: ListSkeletonProps) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  );
}

export interface TableSkeletonProps {
  rows?: number;
  columns?: number;
}

export function TableSkeleton({ rows = 5, columns = 4 }: TableSkeletonProps) {
  return (
    <div className="space-y-2">
      {/* Header */}
      <div className="flex gap-4 px-4 py-3 bg-surface-container-high rounded-t-lg">
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={i} variant="text" className="h-4 w-24 flex-1" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, row) => (
        <div key={row} className="flex gap-4 px-4 py-3 border-b border-outline">
          {Array.from({ length: columns }).map((_, col) => (
            <Skeleton key={col} variant="text" className="h-4 w-24 flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}