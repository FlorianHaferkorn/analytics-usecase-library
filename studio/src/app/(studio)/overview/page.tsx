import { Metadata } from 'next';
import { auth } from '@/lib/auth/config';
import { buildOverviewBundle } from '@/lib/studio/build-overview-data';
import { FrameworkOverview } from '@/components/ui/framework-overview';

export const metadata: Metadata = {
  title: 'Overview | Studio',
};

export default async function OverviewPage() {
  const session = await auth();
  const userName =
    session?.user?.name ?? session?.user?.email?.split('@')[0] ?? 'there';

  const bundle = await buildOverviewBundle();

  return (
    <FrameworkOverview
      userName={userName}
      stats={bundle.stats}
      domains={bundle.domains}
      topKpis={bundle.topKpis}
      activity={bundle.activity}
      auditSparkline={bundle.auditSparkline}
      drift={bundle.drift}
    />
  );
}
