'use client';

import { ButtonHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';
import { Loader2 } from 'lucide-react';

export type ButtonVariant =
  | 'primary'
  | 'secondary'
  | 'ghost'
  | 'destructive'
  | 'outline';

export type ButtonSize = 'sm' | 'md' | 'lg' | 'icon';

export interface ButtonProps
  extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'children'> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  children: React.ReactNode;
  fullWidth?: boolean;
  ref?: React.Ref<HTMLButtonElement>;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    'bg-primary text-on-primary hover:bg-primary-hover active:bg-primary-active',
  secondary:
    'bg-secondary-container text-on-secondary-container hover:bg-secondary-hover active:bg-secondary',
  ghost: 'bg-transparent text-on-surface hover:bg-surface-container-high active:bg-surface-container-highest',
  destructive:
    'bg-error-container text-on-error-container hover:bg-error active:bg-error',
  outline:
    'bg-transparent border border-outline text-on-surface hover:bg-surface-container-high active:bg-surface-container-highest',
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-sm rounded-sm min-h-[40px] min-w-[40px]',
  md: 'px-4 py-2 text-base rounded-md min-h-[44px] min-w-[44px]',
  lg: 'px-6 py-3 text-lg rounded-lg min-h-[48px] min-w-[48px]',
  icon: 'p-2 rounded-full min-h-[44px] min-w-[44px]',
};

export const Button = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled,
  children,
  fullWidth = false,
  className,
  onClick,
  ref,
  ...props
}: ButtonProps) => {
  const isDisabled = disabled || loading;

  return (
    <button
      ref={ref}
      type="button"
      className={cn(
        'inline-flex items-center justify-center font-medium',
        'transition-colors duration-fast ease-out-quick',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2',
        'disabled:opacity-38 disabled:pointer-events-none',
        'active:scale-[0.98]',
        variantStyles[variant],
        sizeStyles[size],
        fullWidth && 'w-full',
        className
      )}
      disabled={isDisabled}
      aria-busy={loading}
      aria-disabled={isDisabled}
      onClick={onClick}
      {...props}
    >
      {loading && (
        <Loader2
          className="mr-2 h-4 w-4 animate-spin"
          aria-hidden="true"
        />
      )}
      {children}
    </button>
  );
};

Button.displayName = 'Button';

/* ---------------------------------------------------------------------------
   Explicit Variant Components (per vercel-composition-patterns)
   Usage: <Button.Primary /> instead of <Button variant="primary" />
   --------------------------------------------------------------------------- */

type ExplicitButtonProps = Omit<ButtonProps, 'variant'>;

function createVariantComponent(variant: ButtonVariant) {
  const Component = ({
    children,
    ref,
    ...props
  }: ExplicitButtonProps & { ref?: React.Ref<HTMLButtonElement> }) => (
    <Button ref={ref} variant={variant} {...props}>
      {children}
    </Button>
  );
  Component.displayName = `Button.${variant.charAt(0).toUpperCase() + variant.slice(1)}`;
  return Component;
}

export const ButtonPrimary = createVariantComponent('primary');
export const ButtonSecondary = createVariantComponent('secondary');
export const ButtonGhost = createVariantComponent('ghost');
export const ButtonDestructive = createVariantComponent('destructive');
export const ButtonOutline = createVariantComponent('outline');

/* ---------------------------------------------------------------------------
   Loading State Component
   --------------------------------------------------------------------------- */
export const ButtonLoading = ({
  children,
  ref,
  ...props
}: ExplicitButtonProps & { ref?: React.Ref<HTMLButtonElement> }) => (
  <Button ref={ref} loading {...props}>
    {children}
  </Button>
);
ButtonLoading.displayName = 'Button.Loading';