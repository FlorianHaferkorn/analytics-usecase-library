'use client';

import { useShallowQueryParam } from '@/lib/hooks/use-domain-filter';

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
  const { setParam } = useShallowQueryParam('tab');

  const handleTabClick = (tabId: string) => {
    setParam(tabId);
  };

  return (
    <div className="flex gap-0.5 border-b border-border mb-4 overflow-x-auto">
      {tabs.map((tab) => {
        const active = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            type="button"
            onClick={() => handleTabClick(tab.id)}
            className={`px-3.5 py-2.5 text-[13px] transition-colors flex items-center gap-2 relative shrink-0 ${
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
