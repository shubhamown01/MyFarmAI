'use client';

import { Fragment, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from '@/lib/utils';
import { X } from 'lucide-react';
import { Button } from './Button';
import { createPortal } from 'react-dom';

type DialogSize = 'sm' | 'md' | 'lg' | 'xl' | 'full';

export interface DialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title?: string;
  description?: string;
  children: React.ReactNode;
  size?: DialogSize;
}

const sizeStyles: Record<DialogSize, string> = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
  full: 'max-w-4xl',
};

export function Dialog({
  open,
  onOpenChange,
  title,
  description,
  children,
  size = 'md',
}: DialogProps) {
  const overlayRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const previousActiveElement = useRef<HTMLElement | null>(null);

  // Focus management
  useEffect(() => {
    if (open) {
      previousActiveElement.current = document.activeElement as HTMLElement;
      document.body.style.overflow = 'hidden';
      setTimeout(() => contentRef.current?.focus(), 0);
    } else {
      document.body.style.overflow = '';
      previousActiveElement.current?.focus();
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [open]);

  // Handle Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && open) {
        onOpenChange(false);
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [open, onOpenChange]);

  // Handle click outside
  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === overlayRef.current) {
      onOpenChange(false);
    }
  };

  const dialogContent = (
    <AnimatePresence>
      {open && (
<motion.div
            ref={overlayRef}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15, ease: 'easeOut' }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-scrim/50"
            onClick={handleOverlayClick}
            role="dialog"
            aria-modal="true"
            aria-labelledby={title ? 'dialog-title' : undefined}
            aria-describedby={description ? 'dialog-description' : undefined}
          >
            <motion.div
              ref={contentRef}
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ duration: 0.2, ease: [0.0, 0.0, 0.2, 1] }}
              className={cn(
                'w-full bg-surface-container rounded-xl shadow-elev-4',
                'overflow-hidden',
                sizeStyles[size]
              )}
              tabIndex={-1}
            >
            {(title || description) && (
              <div className="px-6 py-4 border-b border-outline flex items-start justify-between gap-4">
                <div>
                  {title && (
                    <h2 id="dialog-title" className="text-headline-medium font-semibold text-on-surface">
                      {title}
                    </h2>
                  )}
                  {description && (
                    <p id="dialog-description" className="mt-1 text-body-medium text-on-surface-variant">
                      {description}
                    </p>
                  )}
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => onOpenChange(false)}
                  aria-label="Close dialog"
                  className="flex-shrink-0"
                >
                  <X className="w-5 h-5" aria-hidden="true" />
                </Button>
              </div>
            )}
            <div className="px-6 py-4">{children}</div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );

  if (typeof window === 'undefined') return null;

  return createPortal(dialogContent, document.body);
}

/* ---------------------------------------------------------------------------
   Alert Dialog — For destructive confirmations
   --------------------------------------------------------------------------- */

export interface AlertDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  variant?: 'destructive' | 'primary';
}

export function AlertDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  onConfirm,
  variant = 'destructive',
}: AlertDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange} title={title} description={description} size="sm">
      <div className="flex flex-col gap-4">
        <div className="flex gap-3 justify-end pt-2">
          <Button variant="ghost" onClick={() => onOpenChange(false)}>
            {cancelLabel}
          </Button>
          <Button variant={variant} onClick={() => { onConfirm(); onOpenChange(false); }}>
            {confirmLabel}
          </Button>
        </div>
      </div>
    </Dialog>
  );
}