'use client';

import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from '@/lib/utils';
import { X, CheckCircle, AlertCircle, AlertTriangle, Info } from 'lucide-react';
import { Button } from './Button';

export type ToastVariant = 'success' | 'error' | 'warning' | 'info';

export interface ToastProps {
  variant: ToastVariant;
  message: string;
  action?: { label: string; onClick: () => void };
  onDismiss: () => void;
  duration?: number;
}

const variantIcons: Record<ToastVariant, React.ReactNode> = {
  success: <CheckCircle className="w-5 h-5 flex-shrink-0" aria-hidden="true" />,
  error: <AlertCircle className="w-5 h-5 flex-shrink-0" aria-hidden="true" />,
  warning: <AlertTriangle className="w-5 h-5 flex-shrink-0" aria-hidden="true" />,
  info: <Info className="w-5 h-5 flex-shrink-0" aria-hidden="true" />,
};

const variantStyles: Record<ToastVariant, string> = {
  success: 'bg-success-container text-on-success-container',
  error: 'bg-error-container text-on-error-container',
  warning: 'bg-warning-container text-on-warning-container',
  info: 'bg-info-container text-on-info-container',
};

export function Toast({ variant, message, action, onDismiss, duration = 5000 }: ToastProps) {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false);
      setTimeout(onDismiss, 300); // Wait for exit animation
    }, duration);
    return () => clearTimeout(timer);
  }, [duration, onDismiss]);

  if (!visible) return null;

  return (
    <AnimatePresence mode="wait">
      <motion.div
        initial={{ opacity: 0, x: 100 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 100 }}
        transition={{ duration: 0.2, ease: 'easeOut' }}
        className={cn(
          'fixed bottom-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-lg shadow-elev-4',
          'min-w-[300px] max-w-md',
          variantStyles[variant]
        )}
        role="alert"
        aria-live="polite"
      >
        {variantIcons[variant]}
        <p className="text-body-medium flex-1">{message}</p>
        {action && (
          <Button variant="ghost" size="sm" onClick={action.onClick} className="ml-2">
            {action.label}
          </Button>
        )}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => {
            setVisible(false);
            setTimeout(onDismiss, 200);
          }}
          aria-label="Dismiss"
          className="ml-2 p-1 rounded hover:bg-black/10"
        >
          <X className="w-4 h-4" aria-hidden="true" />
        </Button>
      </motion.div>
    </AnimatePresence>
  );
}

/* ---------------------------------------------------------------------------
   Toast Container — Manages multiple toasts
   --------------------------------------------------------------------------- */

interface ToastItem extends ToastProps {
  id: string;
}

export function ToastContainer({ toasts, onDismiss }: { toasts: ToastItem[]; onDismiss: (id: string) => void }) {
  const isBrowser = typeof window !== 'undefined';

  if (!isBrowser) {
    return null;
  }

  return createPortal(
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2" aria-live="polite" aria-atomic="true">
      <AnimatePresence>
        {toasts.map((toast) => (
          <Toast
            key={toast.id}
            {...toast}
            onDismiss={() => onDismiss(toast.id)}
          />
        ))}
      </AnimatePresence>
    </div>,
    document.body
  );
}

/* ---------------------------------------------------------------------------
   Toast Hook — For easy usage in components
   --------------------------------------------------------------------------- */

import { useCallback } from 'react';

type ToastOptions = Omit<ToastProps, 'variant' | 'message' | 'onDismiss'> & { onDismiss?: () => void };

export function useToast() {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback(
    (variant: ToastVariant, message: string, options: ToastOptions = {}) => {
      const id = crypto.randomUUID();
      const toast: ToastItem = {
        id,
        variant,
        message,
        onDismiss: () => dismiss(id),
        duration: options.duration ?? 5000,
        action: options.action,
      };
      setToasts((prev) => [...prev, toast]);
      return id;
    },
    [dismiss]
  );

  const success = useCallback(
    (message: string, options?: ToastOptions) =>
      showToast('success', message, options),
    [showToast]
  );

  const error = useCallback(
    (message: string, options?: ToastOptions) =>
      showToast('error', message, options),
    [showToast]
  );

  const warning = useCallback(
    (message: string, options?: ToastOptions) =>
      showToast('warning', message, options),
    [showToast]
  );

  const info = useCallback(
    (message: string, options?: ToastOptions) =>
      showToast('info', message, options),
    [showToast]
  );

  return { toasts, dismiss, showToast, success, error, warning, info };
}