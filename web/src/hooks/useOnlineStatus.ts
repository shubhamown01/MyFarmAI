'use client';

import { useEffect, useState } from 'react';

export function useOnlineStatus(): { isOnline: boolean; wasOffline: boolean } {
  // Start online for both the server render and the first client render so
  // hydration matches; the real status is applied after mount. Reading
  // navigator.onLine during render breaks SSR: Node 21+ defines `navigator`
  // without `onLine`, so the server would render an offline state.
  const [isOnline, setIsOnline] = useState(true);

  const [wasOffline, setWasOffline] = useState(false);

  useEffect(() => {
    setIsOnline(navigator.onLine);

    const handleOnline = () => {
      setIsOnline(true);
      setWasOffline(true);
    };

    const handleOffline = () => {
      setIsOnline(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return { isOnline, wasOffline };
}