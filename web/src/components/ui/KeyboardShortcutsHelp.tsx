'use client';

import { useState, useCallback, useEffect } from 'react';
import { Dialog } from './Dialog';
import { Button } from './Button';
import { Keyboard, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { KeyboardShortcut } from '@/hooks/useKeyboardShortcuts';

interface ShortcutGroup {
  category: KeyboardShortcut['category'];
  label: string;
  icon: React.ReactNode;
  shortcuts: KeyboardShortcut[];
}

const categoryConfig: Record<KeyboardShortcut['category'], { label: string; icon: React.ReactNode }> = {
  navigation: { label: 'Navigation', icon: <Keyboard className="w-4 h-4" aria-hidden="true" /> },
  chat: { label: 'Chat', icon: <span className="text-lg" role="img" aria-label="chat">💬</span> },
  voice: { label: 'Voice', icon: <span className="text-lg" role="img" aria-label="voice">🎤</span> },
  global: { label: 'Global', icon: <span className="text-lg" role="img" aria-label="global">🌐</span> },
};

function formatShortcut(shortcut: KeyboardShortcut): string {
  const parts: string[] = [];
  if (shortcut.ctrlKey || shortcut.metaKey) parts.push('⌘');
  if (shortcut.shiftKey) parts.push('⇧');
  if (shortcut.altKey) parts.push('⌥');
  
  const key = shortcut.key.toLowerCase();
  const displayKey: Record<string, string> = {
    ' ': 'Space',
    'enter': 'Enter',
    'escape': 'Esc',
    'tab': 'Tab',
    'backspace': 'Backspace',
    'delete': 'Del',
    'arrowup': '↑',
    'arrowdown': '↓',
    'arrowleft': '←',
    'arrowright': '→',
  };
  
  parts.push(displayKey[key] ?? shortcut.key.toUpperCase());
  return parts.join(' + ');
}

function ShortcutRow({ shortcut }: { shortcut: KeyboardShortcut }) {
  return (
    <tr className="border-t border-outline/50">
      <td className="px-4 py-3 text-body-medium text-on-surface">
        {shortcut.description}
      </td>
      <td className="px-4 py-3 text-right">
        <kbd className={cn(
          'inline-flex items-center gap-1 px-2 py-1',
          'text-xs font-mono font-medium',
          'bg-surface-container-highest text-on-surface-variant',
          'rounded border border-outline',
          'whitespace-nowrap'
        )}>
          {formatShortcut(shortcut)}
        </kbd>
      </td>
    </tr>
  );
}

function ShortcutCategory({ group }: { group: ShortcutGroup }) {
  return (
    <tbody>
      <tr>
        <th
          colSpan={2}
          className="px-4 py-2 text-left text-label-large font-semibold text-on-surface-variant uppercase tracking-wide"
        >
          <div className="flex items-center gap-2">
            {group.icon}
            {group.label}
          </div>
        </th>
      </tr>
      {group.shortcuts.map((shortcut) => (
        <ShortcutRow key={`${shortcut.category}-${shortcut.key}-${shortcut.ctrlKey}-${shortcut.shiftKey}`} shortcut={shortcut} />
      ))}
    </tbody>
  );
}

export interface KeyboardShortcutsHelpProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  shortcuts?: KeyboardShortcut[];
  triggerRef?: React.RefObject<HTMLButtonElement | null>;
}

export function KeyboardShortcutsHelp({
  open,
  onOpenChange,
  shortcuts = [],
  triggerRef,
}: KeyboardShortcutsHelpProps) {
  const [isOpen, setIsOpen] = useState(open);

  useEffect(() => {
    setIsOpen(open);
  }, [open]);

  const handleOpenChange = useCallback((newOpen: boolean) => {
    setIsOpen(newOpen);
    onOpenChange(newOpen);
  }, [onOpenChange]);

  const groupedShortcuts: ShortcutGroup[] = (
    ['navigation', 'chat', 'voice', 'global'] as const
  ).map((category) => {
    const categoryShortcuts = shortcuts.filter((s) => s.category === category);
    if (categoryShortcuts.length === 0) return null;
    const { label, icon } = categoryConfig[category];
    return { category, label, icon, shortcuts: categoryShortcuts };
  }).filter((g): g is ShortcutGroup => g !== null);

  return (
    <Dialog
      open={isOpen}
      onOpenChange={handleOpenChange}
      title="Keyboard Shortcuts"
      description="Quick reference for all available keyboard shortcuts"
      size="lg"
    >
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-sm text-on-surface-variant">
            <Keyboard className="w-4 h-4" aria-hidden="true" />
            <span>Press <kbd className="px-1.5 py-0.5 bg-surface-container-highest rounded border border-outline font-mono">?</kbd> anytime to open this dialog</span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse" role="table">
            {groupedShortcuts.map((group) => (
              <ShortcutCategory key={group.category} group={group} />
            ))}
          </table>
        </div>

        {groupedShortcuts.length === 0 && (
          <div className="text-center py-8 text-on-surface-variant">
            No shortcuts configured
          </div>
        )}
      </div>
    </Dialog>
  );
}

export function KeyboardShortcutsTrigger({
  onClick,
  className,
  'aria-label': ariaLabel = 'Show keyboard shortcuts',
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { onClick: () => void }) {
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={onClick}
      aria-label={ariaLabel}
      className={cn('gap-1', className)}
      {...props}
    >
      <Keyboard className="w-5 h-5" aria-hidden="true" />
      <span className="hidden sm:inline text-body-medium">Shortcuts</span>
    </Button>
  );
}

KeyboardShortcutsTrigger.displayName = 'KeyboardShortcutsTrigger';
KeyboardShortcutsHelp.displayName = 'KeyboardShortcutsHelp';