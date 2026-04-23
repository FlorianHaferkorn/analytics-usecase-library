'use client';

import { useState } from 'react';
import { RoiPresetPanel } from '@/components/roi/roi-preset-panel';
import { SteeringHubClient } from '@/app/(studio)/steering/steering-hub-client';
import { SpineNodeCard } from '@/components/spine/spine-node-card';
import { GoldenThreadTab } from '@/components/blueprint/golden-thread-tab';
import type { DecisionSpine } from '@/lib/schemas/decision-spine';

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
  actionNames: Record<string, string>;
  initialSelectedBracket?: string | null;
  draftBracketId?: string | null;
  golden20Ids: string[];
  spines: DecisionSpine[];
}

type BlueprintTab = 'steering' | 'decision-spine' | 'golden-thread';

const TABS: { id: BlueprintTab; label: string }[] = [
  { id: 'steering', label: 'Steering' },
  { id: 'decision-spine', label: 'Decision Spine' },
  { id: 'golden-thread', label: 'Golden Thread' },
];

// ─── Decision Spine Tab content ───────────────────────────────────────────────

function DecisionSpineTab({ spines }: { spines: DecisionSpine[] }) {
  if (spines.length === 0) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: 240,
          color: 'var(--ink-4)',
          fontSize: 13,
          gap: 8,
          textAlign: 'center',
        }}
      >
        <span style={{ fontSize: 24 }}>⬡</span>
        <span>No decision spines found</span>
      </div>
    );
  }

  return (
    <div style={{ overflow: 'auto', flex: 1, padding: '0 var(--pad) var(--pad)' }}>
      <div style={{ maxWidth: 760, margin: '0 auto', paddingTop: 16 }}>
        <p style={{ fontSize: 13, color: 'var(--ink-3)', marginBottom: 20, lineHeight: 1.6 }}>
          {spines.length} decision spine{spines.length !== 1 ? 's' : ''} loaded from{' '}
          <code style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>
            core/action_codes/decision_spines/
          </code>
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {spines.map((spine) => (
            <SpineNodeCard key={spine.id} spine={spine} compact />
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── BlueprintClient ──────────────────────────────────────────────────────────

/**
 * BlueprintClient — wraps the SteeringHubClient and adds the
 * ROI Preset Panel sidebar for Golden-20 KPI selection.
 * Also provides a "Decision Spine" tab listing all decision spines.
 */
export function BlueprintClient({
  golden20Ids,
  spines,
  brackets,
  actionNames,
  kpiNames,
  ...steeringProps
}: Props) {
  const [selectedKpiId, setSelectedKpiId] = useState<string | null>(
    golden20Ids[0] ?? null
  );
  const [activeTab, setActiveTab] = useState<BlueprintTab>('steering');

  const domains = Array.from(new Set(brackets.map((b) => b.domain))).sort();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Tab bar */}
      <div
        style={{
          display: 'flex',
          gap: 2,
          borderBottom: '1px solid var(--line)',
          padding: '0 var(--pad)',
          flexShrink: 0,
          background: 'var(--bg)',
        }}
      >
        {TABS.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: '10px 14px',
                border: 'none',
                background: 'transparent',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: isActive ? 500 : 400,
                color: isActive ? 'var(--ink)' : 'var(--ink-3)',
                borderBottom: isActive
                  ? '1.5px solid var(--accent)'
                  : '1.5px solid transparent',
                marginBottom: -1,
                transition: 'color 120ms',
                whiteSpace: 'nowrap',
              }}
            >
              {tab.label}
              {tab.id === 'decision-spine' && spines.length > 0 && (
                <span
                  style={{
                    marginLeft: 6,
                    fontSize: 10,
                    color: 'var(--ink-4)',
                    background: 'var(--bg-2)',
                    padding: '1px 5px',
                    borderRadius: 4,
                    fontFamily: 'var(--font-mono)',
                  }}
                >
                  {spines.length}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      <div style={{ flex: 1, display: 'flex', minHeight: 0, overflow: 'hidden' }}>
        {activeTab === 'steering' && (
          <div style={{ display: 'flex', gap: 'var(--gap)', flex: 1, minWidth: 0, alignItems: 'flex-start', overflow: 'auto' }}>
            {/* Main steering area */}
            <div style={{ flex: 1, minWidth: 0 }}>
              <SteeringHubClient {...steeringProps} brackets={brackets} kpiNames={kpiNames} />
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
        )}

        {activeTab === 'decision-spine' && (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
            <DecisionSpineTab spines={spines} />
          </div>
        )}

        {activeTab === 'golden-thread' && (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
            <GoldenThreadTab
              brackets={brackets}
              kpiNames={kpiNames ?? {}}
              actionNames={actionNames}
              domains={domains}
            />
          </div>
        )}
      </div>
    </div>
  );
}
