import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ExternalHandoffPanel } from '@/components/delivery/external-handoff-panel';
import type { PackageSnapshot } from '@/lib/bridge/project-package-repository';

const base: PackageSnapshot = {
  revision: { revision_hash: 'a'.repeat(64), package_id: 'package_demo', project_ref: 'project_demo', revision: 1, parent_revision_hash: null },
  files: [],
};

function withHandoff(drift: string[]): PackageSnapshot {
  const value = {
    record_type: 'external_delivery_handoff_snapshot', use_case_ref: 'uc2_esg',
    authority: { ref: 'Deliverables/_LEDGER.md', sha256: 'b'.repeat(64) },
    required_sources: [{ key: 'source', ref: 'contracts/source.json', sha256: 'c'.repeat(64) }],
    executable_package_file_count: 117, open_gate_refs: ['O-58', 'O-63'],
    integrity_state: drift.length ? 'needs_attention' : 'hashes_match', drift,
    evidence_level: 'static_handoff_inventory', apply_ready: false,
    runtime_proven: false, customer_accepted: false,
  };
  return { ...base, files: [{ path: 'handoff/uc2_esg.json', sha256: 'd'.repeat(64), size: 1,
    encoding: 'base64', contentBase64: btoa(JSON.stringify(value)) }] };
}

describe('external handoff panel', () => {
  it('shows source drift and keeps delivery gates visibly separate', () => {
    render(<ExternalHandoffPanel snapshot={withHandoff(['handoff_manifest:ledger'])} />);
    expect(screen.getByText(/Source integrity: Review required/)).toBeTruthy();
    expect(screen.getByText(/Changed or missing source inventory: ledger/)).toBeTruthy();
    expect(screen.getByText(/2 Ledger-linked open questions/)).toBeTruthy();
    expect(screen.getByText(/External delivery handoff · UC2 · ESG/)).toBeTruthy();
    expect(screen.getByText(/Runtime proof, Apply authorization and customer acceptance remain separate/)).toBeTruthy();
  });

  it('does not equate matching hashes with delivery acceptance', () => {
    render(<ExternalHandoffPanel snapshot={withHandoff([])} />);
    expect(screen.getByText(/Hashes matched at import/)).toBeTruthy();
    expect(screen.getByText(/contract inventory only/)).toBeTruthy();
  });

  it('ignores malformed or falsely approved handoff payloads', () => {
    const snapshot = withHandoff([]);
    snapshot.files[0].contentBase64 = btoa(JSON.stringify({ record_type: 'external_delivery_handoff_snapshot', apply_ready: true }));
    const { container } = render(<ExternalHandoffPanel snapshot={snapshot} />);
    expect(container.textContent).toBe('');
  });
});
