'use client';

import { useState } from 'react';
import dynamic from 'next/dynamic';
import type { LineageGraph } from '@/lib/core/lineage-builder';
import type { DataContract } from '@/lib/schemas';
import { ContractDetailList } from '@/components/lineage/contract-detail';

const LineageFlow = dynamic(
  () => import('@/components/lineage/lineage-flow').then((m) => ({ default: m.LineageFlow })),
  { ssr: false },
);

interface Props {
  graph: LineageGraph;
  contracts: DataContract[];
}

type Tab = 'lineage' | 'contracts';

export function LineageClient({ graph, contracts }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>('lineage');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)', height: 'calc(100vh - 56px - var(--sp-6))' }}>
      {/* Tab bar */}
      <div style={{ display: 'flex', gap: 'var(--sp-1)' }}>
        {[
          { id: 'lineage' as Tab, label: `Lineage Graph (${graph.nodes.length} nodes)` },
          { id: 'contracts' as Tab, label: `Data Contracts (${contracts.length})` },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: 'var(--sp-1) var(--sp-2)',
              backgroundColor: activeTab === tab.id ? 'var(--slate-700)' : 'var(--slate-800)',
              border: `1px solid ${activeTab === tab.id ? 'var(--info)' : 'var(--slate-700)'}`,
              borderRadius: 'var(--radius-md)',
              color: activeTab === tab.id ? 'var(--slate-50)' : 'var(--slate-400)',
              fontSize: '0.8125rem',
              fontWeight: activeTab === tab.id ? 600 : 400,
              cursor: 'pointer',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={{ flex: 1, minHeight: 0 }}>
        {activeTab === 'lineage' ? (
          <LineageFlow graph={graph} />
        ) : (
          <div style={{ overflow: 'auto', height: '100%' }}>
            <ContractDetailList contracts={contracts} />
          </div>
        )}
      </div>
    </div>
  );
}
