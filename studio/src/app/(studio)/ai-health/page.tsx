import { Metadata } from 'next';
import { buildAiHealth } from '@/lib/ai/health';
import { AiHealthPanel } from '@/components/ai/ai-health-panel';

export const metadata: Metadata = {
  title: 'AI-Health | Studio',
};

export default async function AiHealthPage() {
  const health = buildAiHealth();
  return <AiHealthPanel health={health} />;
}
