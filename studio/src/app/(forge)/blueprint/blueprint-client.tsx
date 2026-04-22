'use client';

import { useState } from 'react';
import { RoiPresetPanel } from '@/components/roi/roi-preset-panel';
import { SteeringHubClient } from '@/app/(studio)/steering/steering-hub-client';

interface BracketData {
  id: string;
  title: string;
  domain: string;
  strategicKpiId: string;
  impactDirection: string;
  influencingKpiIds: string[];
  actionCodeIds: string[];
}

interface Props {
  strategyAnchor: string;
  brackets: BracketData[];
  actionDetails: Array<[string, { name: string; status: string; domain: string; triggerKpis: string[] }]>;
  bracketYamls: Record<string, string>;
  kpiNames?: Record<string, string>;
  initialSelectedBracket?: string | null;
  draftBracketId?: string | null;
  golden20Ids: string[];
}

/**
 * BlueprintClient — wraps the SteeringHubClient and adds the
 * ROI Preset Panel sidebar for Golden-20 KPI selection.
 */
export function BlueprintClient({
  golden20Ids,
  ...steeringProps
}: Props) {
  const [selectedKpiId, setSelectedKpiId] = useState<string | null>(
    golden20Ids[0] ?? null
  );

  return (
    <div style={{ display: 'flex', gap: 'var(--sp-2)', height: '100%', alignItems: 'flex-start' }}>
      {/* Main steering area */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <SteeringHubClient {...steeringProps} />
      </div>

      {/* ROI preset panel */}
      <div style={{ flexShrink: 0, width: 360, position: 'sticky', top: 0 }}>
        <RoiPresetPanel
          kpiId={selectedKpiId}
          golden20Ids={golden20Ids}
          onKpiChange={setSelectedKpiId}
        />
      </div>
    </div>
  );
}
