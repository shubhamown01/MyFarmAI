'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Bell, Menu, Search } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useProfile } from '@/hooks/useProfile';
import { BrandMark } from '@/components/Icons/FarmIcons';

export interface TopBarProps {
  onMenuClick?: () => void;
}

export function TopBar({ onMenuClick }: TopBarProps) {
  const router = useRouter();
  const { profile } = useProfile();
  const [query, setQuery] = useState('');
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const notificationsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        searchInputRef.current?.focus();
      }
      if (event.key === 'Escape') {
        setNotificationsOpen(false);
      }
    };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, []);

  useEffect(() => {
    if (!notificationsOpen) return;

    const onPointerDown = (event: MouseEvent) => {
      if (
        notificationsRef.current &&
        !notificationsRef.current.contains(event.target as Node)
      ) {
        setNotificationsOpen(false);
      }
    };
    document.addEventListener('mousedown', onPointerDown);
    return () => document.removeEventListener('mousedown', onPointerDown);
  }, [notificationsOpen]);

  const handleSearch = (event: React.FormEvent) => {
    event.preventDefault();
    const question = query.trim();
    if (!question) {
      searchInputRef.current?.focus();
      return;
    }
    router.push(`/assistant?q=${encodeURIComponent(question)}`);
    setQuery('');
  };

  const searchField = (
    <form onSubmit={handleSearch} role="search" className="w-full">
      <label htmlFor="global-search" className="sr-only">
        Ask about crops, pests, weather, or farming practices
      </label>
      <div className="relative">
        <Search
          className="pointer-events-none absolute left-3.5 top-1/2 h-[18px] w-[18px] -translate-y-1/2 text-on-surface-variant"
          aria-hidden="true"
        />
        <input
          ref={searchInputRef}
          id="global-search"
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Ask about crops, pests, weather, or farming practices..."
          autoComplete="off"
          enterKeyHint="search"
          className="h-11 w-full rounded-xl border border-outline bg-surface-container-low pl-10 pr-4 text-[14px] text-on-surface placeholder:text-on-surface-variant/80 transition-colors hover:border-outline-strong focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/25 sm:text-[15px]"
        />
      </div>
    </form>
  );

  return (
    <header className="sticky top-0 z-20 border-b border-outline bg-surface/95 backdrop-blur-md">
      <div className="flex h-16 items-center gap-3 px-4 sm:px-6 lg:h-[88px] lg:gap-6 lg:px-8">
        <button
          type="button"
          onClick={onMenuClick}
          className="inline-flex h-10 w-10 flex-none items-center justify-center rounded-xl text-on-surface transition-colors hover:bg-surface-container-high focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary lg:hidden"
          aria-label="Open navigation menu"
        >
          <Menu className="h-5 w-5" aria-hidden="true" />
        </button>

        <Link
          href="/"
          className="inline-flex flex-none items-center gap-2 text-lg font-bold tracking-[-0.02em] text-on-surface lg:hidden"
          aria-label="MyFarmAI home"
        >
          <BrandMark className="h-7 w-7" />
          <span className="hidden sm:inline">MyFarmAI</span>
        </Link>

        <div className="mx-auto hidden w-full max-w-[760px] md:block">{searchField}</div>

        <div className="ml-auto flex flex-none items-center gap-1.5 sm:gap-2">
          <div className="relative" ref={notificationsRef}>
            <button
              type="button"
              onClick={() => setNotificationsOpen((open) => !open)}
              className={cn(
                'inline-flex h-10 w-10 items-center justify-center rounded-full text-on-surface-variant transition-colors hover:bg-surface-container-high hover:text-on-surface',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary',
                notificationsOpen && 'bg-surface-container-high text-on-surface',
              )}
              aria-label="Notifications"
              aria-expanded={notificationsOpen}
              aria-controls="notifications-panel"
            >
              <Bell className="h-[21px] w-[21px]" aria-hidden="true" />
            </button>

            {notificationsOpen && (
              <div
                id="notifications-panel"
                role="region"
                aria-label="Notifications"
                className="absolute right-0 top-12 w-[min(320px,calc(100vw-2rem))] rounded-2xl border border-outline bg-surface p-4 shadow-elev-3"
              >
                <p className="text-sm font-semibold text-on-surface">Notifications</p>
                <p className="mt-1.5 text-[13px] leading-5 text-on-surface-variant">
                  Notifications are not connected yet. This app has no notification service,
                  so there is nothing to show.
                </p>
              </div>
            )}
          </div>

          <Link
            href="/settings"
            className="inline-flex h-9 w-9 flex-none items-center justify-center rounded-full border border-outline bg-surface-container-high text-sm font-semibold uppercase text-on-surface-variant transition-colors hover:border-outline-strong hover:text-on-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 sm:h-10 sm:w-10"
            aria-label="Open profile settings"
            title={`${profile.name} — profile settings`}
          >
            {profile.name.charAt(0) || 'S'}
          </Link>
        </div>
      </div>

      <div className="border-t border-outline px-4 py-2.5 md:hidden">{searchField}</div>
    </header>
  );
}
