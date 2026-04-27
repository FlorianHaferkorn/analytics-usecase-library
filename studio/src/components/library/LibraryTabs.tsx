'use client';

import { useRouter, useSearchParams } from 'next/navigation';

interface Tab {
  id: string;
  label: string;
  count: number;
}

interface LibraryTabsProps {
  tabs: Tab[];
  activeTab: string;
}

export function LibraryTabs({ tabs, activeTab }: LibraryTabsProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const handleTabClick = (tabId: string) => {
    const current = new URLSearchParams(searchParams);
    current.set('tab', tabId);
    router.push(`?${current.toString()}`);
  };

  return (
    <div className="flex gap-1 border-b border-border mb-4">
      {tabs.map((tab) => {
        const active = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            onClick={() => handleTabClick(tab.id)}
            className={`px-3.5 py-2.5 text-xs font-medium transition-colors flex items-center gap-2 relative ${
              active
                ? 'text-foreground'
                : 'text-foreground-muted hover:text-foreground'
            }`}
            style={{
              borderBottom: active ? '2px solid var(--accent)' : '2px solid transparent',
              marginBottom: '-2px',
            }}
          >
            {tab.label}
            <span
              className="text-2xs font-mono"
              style={{ opacity: active ? 1 : 0.7 }}
            >
              {tab.count}
            </span>
          </button>
        );
      })}
    </div>
  );
}
