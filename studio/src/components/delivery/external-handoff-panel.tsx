'use client';

import Link from 'next/link';
import { StudioPanel } from '@/components/ui/studio-page';
import type { PackageSnapshot } from '@/lib/bridge/project-package-repository';

interface ExternalHandoff {
  record_type: 'external_delivery_handoff_snapshot';
  use_case_ref: string;
  authority: { ref: string; sha256: string };
  required_sources: Array<{ key: string; ref: string; sha256: string }>;
  executable_package_file_count: number;
  open_gate_refs: string[];
  integrity_state: 'hashes_match' | 'needs_attention';
  drift: string[];
  evidence_level: string;
  apply_ready: false;
  runtime_proven: false;
  customer_accepted: false;
}

function formatUseCaseLabel(reference: string): string {
  const match = /^uc(\d+)(?:_(.+))?$/.exec(reference);
  if (!match) return reference.replaceAll('_', ' ');
  const suffix = (match[2] ?? '').split('_').filter(Boolean).map((part) =>
    part.length <= 4 ? part.toUpperCase() : part[0].toUpperCase() + part.slice(1)
  ).join(' ');
  return `UC${match[1]}${suffix ? ` · ${suffix}` : ''}`;
}

function driftLabel(value: string): string {
  const [, scope] = value.split(':', 2);
  return (scope ?? value).replaceAll('_', ' ');
}

function readHandoffs(snapshot: PackageSnapshot): ExternalHandoff[] {
  const handoffs: ExternalHandoff[] = [];
  for (const file of snapshot.files.filter((item) => /^handoff\/[a-z][a-z0-9_]{0,63}\.json$/.test(item.path))) {
    try {
      const binary = atob(file.contentBase64);
      const bytes = Uint8Array.from(binary, (character) => character.charCodeAt(0));
      const value = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes)) as ExternalHandoff;
      if (value.record_type !== 'external_delivery_handoff_snapshot' || file.path !== `handoff/${value.use_case_ref}.json`
        || typeof value.authority?.ref !== 'string' || typeof value.executable_package_file_count !== 'number'
        || !['hashes_match', 'needs_attention'].includes(value.integrity_state)
        || !Array.isArray(value.drift) || !value.drift.every((item) => typeof item === 'string')
        || !Array.isArray(value.open_gate_refs) || !value.open_gate_refs.every((item) => typeof item === 'string')
        || !Array.isArray(value.required_sources)
        || value.apply_ready !== false || value.runtime_proven !== false || value.customer_accepted !== false) continue;
      handoffs.push(value);
    } catch {
      continue;
    }
  }
  return handoffs;
}

export function ExternalHandoffPanel({ snapshot }: { snapshot: PackageSnapshot }) {
  const handoffs = readHandoffs(snapshot);
  if (!handoffs.length) return null;
  return (
    <div style={{ display: 'grid', gap: 'var(--gap)' }}>
      {handoffs.map((handoff) => {
        const attention = handoff.integrity_state !== 'hashes_match';
        return (
          <StudioPanel
            key={handoff.use_case_ref}
            title={`External delivery handoff · ${formatUseCaseLabel(handoff.use_case_ref)}`}
            description="A pinned metadata view of an external handoff. The source ledger and contracts remain authoritative; this is not tenant, Apply, or customer-acceptance evidence."
            compactHeader
          >
            <div style={{ display: 'grid', gap: 'var(--space-3)', fontSize: 'var(--text-sm)' }}>
              <div role="status" style={{ color: attention ? 'var(--warning)' : 'var(--ink)' }}>
                <strong>Source integrity: {attention ? 'Review required' : 'Hashes matched at import'}</strong>
                {' · '}{handoff.required_sources.length} source contracts, {handoff.executable_package_file_count} package files
              </div>
              <div title={handoff.authority.ref}>Authority: project Ledger · {handoff.open_gate_refs.length} Ledger-linked open questions. <Link href="/architecture">Review the full gate set in Design</Link>.</div>
              {attention && <div>Changed or missing source inventory: {handoff.drift.map(driftLabel).join(', ')}</div>}
              <div>Delivery state: contract inventory only. Runtime proof, Apply authorization and customer acceptance remain separate.</div>
            </div>
          </StudioPanel>
        );
      })}
    </div>
  );
}
