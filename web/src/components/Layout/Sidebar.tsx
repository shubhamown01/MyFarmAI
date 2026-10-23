'use client';

import { useEffect, useRef } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { BrandMark } from '@/components/Icons/FarmIcons';
import {
  BookOpen,
  Bot,
  Bug,
  CloudSun,
  Home,
  Settings,
  Sprout,
  Users,
  X,
} from 'lucide-react';

export interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

const NAVIGATION_ITEMS = [
  { href: '/', label: 'Home', icon: Home },
  { href: '/assistant', label: 'AI Assistant', icon: Bot },
  { href: '/crops', label: 'Crops', icon: Sprout },
  { href: '/weather', label: 'Weather', icon: CloudSun },
  { href: '/pest-disease', label: 'Pest & Disease', icon: Bug },
  { href: '/knowledge', label: 'Knowledge', icon: BookOpen },
  { href: '/community', label: 'Community', icon: Users },
] as const;

function isActivePath(pathname: string, href: string) {
  if (href === '/') return pathname === '/';
  return pathname === href || pathname.startsWith(`${href}/`);
}

function NavigationLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();

  return (
    <ul className="space-y-1.5" role="list">
      {NAVIGATION_ITEMS.map((item) => {
        const active = isActivePath(pathname, item.href);
        const Icon = item.icon;

        return (
          <li key={item.href}>
            <Link
              href={item.href}
              onClick={onNavigate}
              aria-current={active ? 'page' : undefined}
              className={cn(
                'relative flex min-h-11 items-center gap-3 rounded-xl px-4 text-[15px] font-medium',
                'transition-colors duration-fast focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2',
                active
                  ? 'bg-primary-container text-primary-strong'
                  : 'text-on-surface hover:bg-surface-container-high',
              )}
            >
              {active && (
                <span
                  className="absolute left-0 top-2 h-[calc(100%-16px)] w-1 rounded-full bg-primary"
                  aria-hidden="true"
                />
              )}
              <Icon
                className={cn(
                  'h-5 w-5 flex-none',
                  active ? 'text-primary' : 'text-on-surface-variant',
                )}
                strokeWidth={active ? 2.2 : 1.8}
                aria-hidden="true"
              />
              <span className="truncate">{item.label}</span>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}

function SidebarBody({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <div className="flex h-full flex-col">
      <div className="flex h-[72px] items-center px-6 lg:h-[88px]">
        <Link
          href="/"
          onClick={onNavigate}
          className="inline-flex items-center gap-2.5 rounded-lg text-[22px] font-bold tracking-[-0.02em] text-on-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          aria-label="MyFarmAI home"
        >
          <BrandMark className="h-9 w-9" />
          <span>MyFarmAI</span>
        </Link>
      </div>

      <nav className="flex-1 overflow-y-auto px-4 py-5" aria-label="Main navigation">
        <NavigationLinks onNavigate={onNavigate} />
      </nav>

      <div className="border-t border-outline p-4">
        <Link
          href="/settings"
          onClick={onNavigate}
          className="flex min-h-11 items-center gap-3 rounded-xl px-4 text-[15px] font-medium text-on-surface transition-colors hover:bg-surface-container-high focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
        >
          <Settings className="h-5 w-5 flex-none text-on-surface-variant" strokeWidth={1.8} aria-hidden="true" />
          <span>Settings</span>
        </Link>
      </div>
    </div>
  );
}

export function Sidebar({ isOpen = false, onClose }: SidebarProps) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    closeButtonRef.current?.focus();

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose?.();
    };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [isOpen, onClose]);

  return (
    <>
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-[280px] border-r border-outline bg-surface-container lg:block">
        <SidebarBody />
      </aside>

      {isOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            className="absolute inset-0 cursor-default bg-on-surface/35"
            onClick={onClose}
            aria-label="Close navigation menu"
          />
          <aside
            className="relative flex h-full w-[min(86vw,300px)] flex-col border-r border-outline bg-surface-container shadow-elev-4"
            aria-label="Main navigation"
          >
            <button
              ref={closeButtonRef}
              type="button"
              onClick={onClose}
              className="absolute right-3 top-4 inline-flex h-10 w-10 items-center justify-center rounded-full text-on-surface-variant transition-colors hover:bg-surface-container-high hover:text-on-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              aria-label="Close navigation menu"
            >
              <X className="h-5 w-5" aria-hidden="true" />
            </button>
            <SidebarBody onNavigate={onClose} />
          </aside>
        </div>
      )}
    </>
  );
}
