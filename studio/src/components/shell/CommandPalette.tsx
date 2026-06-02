'use client';

import { useState, useEffect, useRef } from 'react';

interface CommandItem {
  id: string;
  label: string;
  category: string;
  action: () => void;
}

interface ExtraCommand {
  id: string;
  label: string;
  category: string;
  action: () => void;
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onNew?: () => void;
  extraCommands?: ExtraCommand[];
}

const DEFAULT_COMMANDS: CommandItem[] = [
  {
    id: 'nav-overview',
    label: 'Go to Overview',
    category: 'Navigation',
    action: () => (window.location.href = '/overview'),
  },
  {
    id: 'nav-canvas',
    label: 'Go to Canvas',
    category: 'Navigation',
    action: () => (window.location.href = '/canvas'),
  },
  {
    id: 'nav-library',
    label: 'Go to Library',
    category: 'Navigation',
    action: () => (window.location.href = '/library'),
  },
  {
    id: 'action-new',
    label: 'New Element',
    category: 'Actions',
    action: () => {},
  },
];

export function CommandPalette({ isOpen, onClose, onNew, extraCommands = [] }: CommandPaletteProps) {
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const allCommands: CommandItem[] = [
    ...DEFAULT_COMMANDS,
    ...extraCommands.map((c) => ({
      id: c.id,
      label: c.label,
      category: c.category,
      action: c.action,
    })),
    {
      id: 'nav-templates',
      label: 'Go to Report Templates',
      category: 'Navigation',
      action: () => {
        window.location.href = '/templates';
      },
    },
  ];

  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
      setQuery('');
      setSelected(0);
    }
  }, [isOpen]);

  const filtered = allCommands.filter(
    (cmd) =>
      cmd.label.toLowerCase().includes(query.toLowerCase()) ||
      cmd.category.toLowerCase().includes(query.toLowerCase())
  );

  const handleSelect = (cmd: CommandItem) => {
    if (cmd.id === 'action-new' && onNew) {
      onNew();
    } else {
      cmd.action();
    }
    onClose();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelected((s) => (s + 1) % filtered.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelected((s) => (s - 1 + filtered.length) % filtered.length);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filtered[selected]) {
        handleSelect(filtered[selected]);
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black/50 z-modal flex items-start justify-center pt-24"
      onClick={onClose}
    >
      <div
        className="w-96 max-h-96 bg-panel rounded-lg shadow-lg border border-border overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search input */}
        <div className="border-b border-border p-4">
          <input
            ref={inputRef}
            type="text"
            placeholder="Search commands…"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelected(0);
            }}
            onKeyDown={handleKeyDown}
            className="w-full bg-bg text-foreground text-sm px-3 py-2 rounded border border-border focus:outline-none focus:border-accent"
          />
        </div>

        {/* Results */}
        <div className="overflow-y-auto flex-1">
          {filtered.length === 0 ? (
            <div className="p-8 text-center text-foreground-subtle text-sm">
              No commands found
            </div>
          ) : (
            <div>
              {filtered.map((cmd, i) => (
                <button
                  key={cmd.id}
                  onClick={() => handleSelect(cmd)}
                  className={`w-full px-4 py-3 text-left border-b border-border last:border-b-0 transition-colors ${
                    i === selected
                      ? 'bg-hover text-foreground'
                      : 'text-foreground-muted hover:bg-hover'
                  }`}
                >
                  <div className="text-xs text-foreground-subtle font-medium mb-1">
                    {cmd.category}
                  </div>
                  <div className="text-sm font-medium">{cmd.label}</div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-border p-3 bg-bg-2 text-2xs text-foreground-subtle flex items-center justify-between">
          <span>Use arrow keys to navigate, Enter to select, Esc to close</span>
        </div>
      </div>
    </div>
  );
}
