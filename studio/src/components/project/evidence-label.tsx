import type { EvidenceKind } from '@/lib/bridge/local-reference';
import styles from './project-automation.module.css';
export function EvidenceLabel({ kind, scope }: { kind: EvidenceKind; scope?: string }) {
  const labels: Record<EvidenceKind, string> = { local_check: 'Locally checked', simulation: 'Simulated', tenant_verified: 'Tenant verified', not_verified: 'Not verified' };
  return <span className={styles.status}>{labels[kind]}{scope ? ` · ${scope}` : ''}</span>;
}
