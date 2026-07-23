'use client';



import { useState, useCallback, useMemo } from 'react';

import Link from 'next/link';

import { RoiPresetPanel } from '@/components/roi/roi-preset-panel';

import { SteeringHubClient } from '@/app/(studio)/steering/steering-hub-client';

import { SpineNodeCard } from '@/components/spine/spine-node-card';

import { GoldenThreadTab } from '@/components/blueprint/golden-thread-tab';

import { StudioPageHeader } from '@/components/ui/studio-page';

import { useDomainFilter } from '@/lib/hooks/use-domain-filter';

import { filterByDomain } from '@/lib/studio/domain-filter';

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



const TABS: { id: BlueprintTab; label: string; hint?: string }[] = [

  { id: 'steering', label: 'Steering', hint: 'Edit brackets & explore flow' },

  { id: 'decision-spine', label: 'Decision Spine', hint: 'Prescriptive playbooks' },

  { id: 'golden-thread', label: 'Golden Thread', hint: 'Portfolio map & coverage' },

];



function DecisionSpineTab({ spines }: { spines: DecisionSpine[] }) {

  if (spines.length === 0) {

    return (

      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: 240, color: 'var(--ink-4)', fontSize: 13, gap: 8, textAlign: 'center' }}>

        <span style={{ fontSize: 24 }}>⬡</span>

        <span>No decision spines found</span>

      </div>

    );

  }



  return (

    <div style={{ overflow: 'auto', flex: 1, padding: 'var(--pad)' }}>

      <div style={{ maxWidth: 760, margin: '0 auto' }}>

        <div style={{ marginBottom: 'var(--gap)', padding: '14px var(--pad)', borderRadius: 'var(--radius)', border: '1px solid var(--line)', background: 'var(--bg-2)' }}>

          <p style={{ margin: 0, fontSize: 13, color: 'var(--ink-2)', lineHeight: 1.6 }}>

            Decision spines are prescriptive playbooks: they connect a strategic question to recommended action patterns.

            They appear automatically in <Link href="/compose" style={{ color: 'var(--accent)' }}>Compose</Link> when you select a matching use case.

            Browse coverage here; govern spine definitions in <Link href="/catalog" style={{ color: 'var(--accent)' }}>Registry → Catalog</Link>.

          </p>

        </div>

        <p style={{ fontSize: 12, color: 'var(--ink-4)', marginBottom: 16 }}>

          {spines.length} spine{spines.length !== 1 ? 's' : ''} from{' '}

          <code style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>core/action_codes/decision_spines/</code>

        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--gap)' }}>

          {spines.map((spine) => (

            <SpineNodeCard key={spine.id} spine={spine} compact />

          ))}

        </div>

      </div>

    </div>

  );

}



export function BlueprintClient({

  golden20Ids,

  spines,

  brackets,

  actionNames,

  kpiNames,

  strategyAnchor,

  actionDetails,

  ...steeringProps

}: Props) {

  const [selectedKpiId, setSelectedKpiId] = useState<string | null>(golden20Ids[0] ?? null);

  const [activeTab, setActiveTab] = useState<BlueprintTab>('steering');



  const handleSelectedBracketChange = useCallback((bracketId: string | null) => {

    if (!bracketId) return;

    const bracket = brackets.find((b) => b.id === bracketId);

    if (bracket && golden20Ids.includes(bracket.strategicKpiId)) {

      setSelectedKpiId(bracket.strategicKpiId);

    }

  }, [brackets, golden20Ids]);



  const { domainFilter } = useDomainFilter();

  const filteredBrackets = useMemo(
    () => filterByDomain(brackets, domainFilter, (b) => b.domain),
    [brackets, domainFilter],
  );

  const domains = Array.from(new Set(brackets.map((b) => b.domain))).sort();
  const headerBadge = domainFilter
    ? `${filteredBrackets.length} of ${brackets.length} · ${domainFilter}`
    : `All ${brackets.length}`;



  return (

    <div className="studio-blueprint-page" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100dvh - var(--shell-header) - var(--pad) * 2)', minHeight: 0, gap: 'var(--gap)' }}>

      <div style={{ padding: '0 var(--pad)', flexShrink: 0 }}>

        <StudioPageHeader

          eyebrow="Forge / Blueprint"

          title="Blueprint"

          description="Navigate the golden thread, refine bracket YAML, and turn draft scaffolds into governed use cases."

          badge={headerBadge}

          tone="success"

          compact

        />

      </div>



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

              type="button"

              onClick={() => setActiveTab(tab.id)}

              title={tab.hint}

              style={{

                padding: '10px 14px',

                border: 'none',

                background: 'transparent',

                cursor: 'pointer',

                fontSize: '0.875rem',

                fontWeight: isActive ? 500 : 400,

                color: isActive ? 'var(--ink)' : 'var(--ink-3)',

                borderBottom: isActive ? '1.5px solid var(--accent)' : '1.5px solid transparent',

                marginBottom: -1,

                transition: 'color 120ms',

                whiteSpace: 'nowrap',

              }}

            >

              {tab.label}

              {tab.id === 'decision-spine' && spines.length > 0 && (

                <span style={{ marginLeft: 6, fontSize: 10, color: 'var(--ink-4)', background: 'var(--bg-2)', padding: '1px 5px', borderRadius: 4, fontFamily: 'var(--font-mono)' }}>

                  {spines.length}

                </span>

              )}

            </button>

          );

        })}

      </div>



      <div style={{ flex: 1, display: 'flex', minHeight: 0, overflow: 'hidden' }}>

        {activeTab === 'steering' && (

          <div className="studio-blueprint-steering" style={{ display: 'flex', gap: 'var(--gap)', flex: 1, minWidth: 0, minHeight: 0, overflow: 'hidden', padding: '0 var(--pad) var(--pad)' }}>

            <div style={{ flex: 1, minWidth: 0, minHeight: 0, display: 'flex', flexDirection: 'column' }}>

              <SteeringHubClient

                {...steeringProps}

                strategyAnchor={strategyAnchor}

                actionDetails={actionDetails}

                brackets={filteredBrackets}

                kpiNames={kpiNames}

                pageEyebrow="Forge / Blueprint"

                onSelectedBracketChange={handleSelectedBracketChange}

                embedded

              />

            </div>

            <div className="studio-blueprint-roi" style={{ flexShrink: 0, width: 360, overflow: 'auto', alignSelf: 'flex-start', position: 'sticky', top: 0 }}>

              <RoiPresetPanel kpiId={selectedKpiId} golden20Ids={golden20Ids} onKpiChange={setSelectedKpiId} />

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

              strategyAnchor={strategyAnchor}

              brackets={filteredBrackets}

              actionDetails={actionDetails}

              kpiNames={kpiNames ?? {}}

              actionNames={actionNames}

              domains={domains}

              activeDomainFilter={domainFilter}

            />

          </div>

        )}

      </div>

    </div>

  );

}

