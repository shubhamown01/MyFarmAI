'use client';

import { motion, AnimatePresence } from 'motion/react';
import { cn } from '@/lib/utils';
import { WifiOff } from 'lucide-react';
import { useOnlineStatus } from '@/hooks/useOnlineStatus';

export function OfflineIndicator(): JSX.Element | null {
  const { isOnline, wasOffline } = useOnlineStatus();

  if (isOnline && !wasOffline) {
    return null;
  }

  if (!isOnline) {
    return (
      <AnimatePresence mode="wait">
        <motion.div
          initial={{ opacity: 0, y: -100 }}
          animate={{ opacity: 1, y: 0 }}
          className={cn(
            'fixed top-0 left-0 right-0 z-50 flex items-center justify-center gap-2 px-4 py-2',
            'text-sm font-medium',
            'bg-warning-container text-on-warning-container border-b border-warning'
          )}
          role="status"
          aria-live="polite"
          aria-atomic="true"
        >
          <WifiOff className="w-4 h-4 flex-shrink-0" aria-hidden="true" />
          <span>You're offline. Changes will sync when reconnected.</span>
          <span className="px-2 py-0.5 text-xs bg-warning text-on-warning rounded-full">
            0 pending
          </span>
        </motion.div>
      </AnimatePresence>
    );
  }

  return (
    <AnimatePresence mode="wait">
      <motion.div
        initial={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -100 }}
        transition={{ duration: 0.3, ease: 'easeOut' }}
        className={cn(
          'fixed top-0 left-0 right-0 z-50 flex items-center justify-center gap-2 px-4 py-2',
          'text-sm font-medium',
          'bg-success-container text-on-success-container border-b border-success'
        )}
        role="status"
        aria-live="polite"
        aria-atomic="true"
      >
        <WifiOff className="w-4 h-4 flex-shrink-0" aria-hidden="true" />
        <span>You're back online. Syncing changes...</span>
      </motion.div>
    </AnimatePresence>
  );
}