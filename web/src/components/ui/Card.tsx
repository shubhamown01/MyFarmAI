'use client';

import { HTMLAttributes, Ref } from 'react';
import { cn } from '@/lib/utils';

export type CardVariant = 'default' | 'elevated' | 'outlined' | 'filled';

export interface CardProps extends Omit<HTMLAttributes<HTMLDivElement>, 'children' | 'ref'> {
  variant?: CardVariant;
  interactive?: boolean;
  onClick?: () => void;
  children: React.ReactNode;
  className?: string;
  ref?: Ref<HTMLDivElement | HTMLButtonElement>;
}

const variantStyles: Record<CardVariant, string> = {
  default: 'bg-surface-container shadow-elev-1',
  elevated: 'bg-surface-container-high shadow-elev-2',
  outlined: 'bg-surface border border-outline shadow-none',
  filled: 'bg-surface-container-highest shadow-none',
};

export const Card = ({
  variant = 'default',
  interactive = false,
  onClick,
  children,
  className,
  ref,
}: CardProps) => {
  const interactiveStyles = interactive
    ? 'transition-all duration-standard ease-out-standard hover:shadow-elev-2 hover:-translate-y-0.5 active:scale-[0.99] active:shadow-elev-1 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2'
    : '';

  if (interactive && onClick) {
    return (
      <button
        ref={ref as Ref<HTMLButtonElement>}
        type="button"
        className={cn(
          'rounded-xl',
          variantStyles[variant],
          interactiveStyles,
          className
        )}
        onClick={onClick}
        role="button"
        tabIndex={0}
      >
        {children}
      </button>
    );
  }

  return (
    <div
      ref={ref as Ref<HTMLDivElement>}
      className={cn(
        'rounded-xl',
        variantStyles[variant],
        className
      )}
    >
      {children}
    </div>
  );
};

Card.displayName = 'Card';

/* ---------------------------------------------------------------------------
   Card Sub-components for Compound Component Pattern
   --------------------------------------------------------------------------- */

interface CardHeaderProps extends HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  ref?: Ref<HTMLDivElement>;
}

export const CardHeader = ({
  children,
  className,
  ref,
  ...props
}: CardHeaderProps) => (
  <div
    ref={ref}
    className={cn('px-6 py-4 border-b border-outline', className)}
    {...props}
  >
    {children}
  </div>
);
CardHeader.displayName = 'CardHeader';

interface CardTitleProps extends HTMLAttributes<HTMLHeadingElement> {
  children: React.ReactNode;
  ref?: Ref<HTMLHeadingElement>;
}

export const CardTitle = ({
  children,
  className,
  ref,
  ...props
}: CardTitleProps) => (
  <h3
    ref={ref}
    className={cn('text-headline-small font-semibold text-on-surface', className)}
    {...props}
  >
    {children}
  </h3>
);
CardTitle.displayName = 'CardTitle';

interface CardDescriptionProps extends HTMLAttributes<HTMLParagraphElement> {
  children: React.ReactNode;
  ref?: Ref<HTMLParagraphElement>;
}

export const CardDescription = ({
  children,
  className,
  ref,
  ...props
}: CardDescriptionProps) => (
  <p
    ref={ref}
    className={cn('mt-1 text-body-medium text-on-surface-variant', className)}
    {...props}
  >
    {children}
  </p>
);
CardDescription.displayName = 'CardDescription';

interface CardContentProps extends HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  ref?: Ref<HTMLDivElement>;
}

export const CardContent = ({
  children,
  className,
  ref,
  ...props
}: CardContentProps) => (
  <div
    ref={ref}
    className={cn('px-6 py-4', className)}
    {...props}
  >
    {children}
  </div>
);
CardContent.displayName = 'CardContent';

interface CardFooterProps extends HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  ref?: Ref<HTMLDivElement>;
}

export const CardFooter = ({
  children,
  className,
  ref,
  ...props
}: CardFooterProps) => (
  <div
    ref={ref}
    className={cn('px-6 py-4 border-t border-outline flex items-center gap-2', className)}
    {...props}
  >
    {children}
  </div>
);
CardFooter.displayName = 'CardFooter';