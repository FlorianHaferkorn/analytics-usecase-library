'use client';

import { useState } from 'react';
import dynamic from 'next/dynamic';
import type { LineageGraph } from '@/lib/core/lineage-builder';
import type { DataContract } from '@/lib/schemas';
import { ContractDetailList } from '@/components/lineage/contract-detail';
import { StudioMetric, StudioMetricBar, StudioPage, StudioPageHeader, StudioPanel, StudioSegmentedControl, StudioToolbar } from '@/components/ui/studio-page';

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
    <StudioPage fill>
      <StudioPageHeader
        eyebrow="Studio / Traceability"
        title="Lineage"
        description="Trace governed entities through the semantic layer and inspect supporting data contracts from one shared navigation surface."
        badge={activeTab === 'lineage' ? `${graph.nodes.length} nodes` : `${contracts.length} contracts`}
        tone="info"
      />

      <StudioMetricBar>
        <StudioMetric label="Nodes" value={graph.nodes.length} meta="in lineage graph" tone="info" />
        <StudioMetric label="Edges" value={graph.edges.length} meta="dependency links" />
        <StudioMetric label="Contracts" value={contracts.length} meta="available for inspection" tone="success" />
        <StudioMetric label="View" value={activeTab} meta={activeTab === 'lineage' ? 'graph exploration' : 'contract detail review'} />
      </StudioMetricBar>

      <StudioToolbar>
        <StudioSegmentedControl
          value={activeTab}
          onChange={setActiveTab}
          options={[
            { value: 'lineage', label: `Lineage Graph (${graph.nodes.length})` },
            { value: 'contracts', label: `Data Contracts (${contracts.length})` },
          ]}
        />
      </StudioToolbar>

      {/* Content */}
      <div style={{ flex: 1, minHeight: 0 }}>
        {activeTab === 'lineage' ? (
          <StudioPanel title="Lineage Graph" description="Navigate the dependency network across KPIs, brackets and supporting artifacts." tone="info" style={{ height: '100%' }}>
            <LineageFlow graph={graph} />
          </StudioPanel>
        ) : (
          <StudioPanel title="Data Contracts" description="Review contract metadata and structure with the same page framing used across Studio." tone="success" style={{ height: '100%' }}>
            <div style={{ overflow: 'auto', height: '100%' }}>
              <ContractDetailList contracts={contracts} />
            </div>
          </StudioPanel>
        )}
      </div>
    </StudioPage>
  );
}
