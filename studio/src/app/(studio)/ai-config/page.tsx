import { Metadata } from 'next';
import { getConfigLayer } from '@/lib/db/ai-config-repo';
import { AiConfigPanel } from '@/components/ai/ai-config-panel';
import type { LayerStatus } from '@/lib/ai/config/governance-types';

export const metadata: Metadata = {
  title: 'AI-Config | Studio',
};

export default async function AiConfigPage() {
  // Tenant (L1) layer for the default project.
  const row = getConfigLayer('default', 'L1', '');
  return (
    <AiConfigPanel
      layer="L1"
      domainId=""
      initialStatus={(row?.status as LayerStatus) ?? 'none'}
      initialConfig={row?.config_json ?? ''}
    />
  );
}
