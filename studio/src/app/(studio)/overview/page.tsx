import { Metadata } from 'next';
import { buildOverviewBundle } from '@/lib/studio/build-overview-data';
import { FrameworkOverview } from '@/components/ui/framework-overview';

export const metadata: Metadata = {
  title: 'Overview | Studio',
};

export default async function OverviewPage() {
  const bundle = await buildOverviewBundle();

  return (
    <FrameworkOverview
      stats={bundle.stats}
      domains={bundle.domains}
      topKpis={bundle.topKpis}
      activity={bundle.activity}
      auditSparkline={bundle.auditSparkline}
      drift={bundle.drift}
    />
  );
}
