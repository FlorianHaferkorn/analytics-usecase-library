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
    <div className="flex gap-0.5 border-b border-border mb-4">
      {tabs.map((tab) => {
        const active = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            onClick={() => handleTabClick(tab.id)}
            className={`px-3.5 py-2.5 text-[13px] transition-colors flex items-center gap-2 relative ${
              active
                ? 'font-medium text-foreground'
                : 'font-normal text-foreground-muted hover:text-foreground'
            }`}
            style={{
              borderBottom: active ? '1.5px solid var(--accent)' : '1.5px solid transparent',
              marginBottom: '-1px',
            }}
          >
            {tab.label}
            <span
              className={`text-2xs font-mono ${active ? 'text-foreground-muted' : 'text-foreground-subtle'}`}
            >
              {tab.count}
            </span>
          </button>
        );
      })}
    </div>
  );
}
