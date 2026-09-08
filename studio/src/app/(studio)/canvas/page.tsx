import { Metadata } from 'next';
import { Suspense } from 'react';
import { buildLineageGraph } from '@/lib/core/lineage-builder';
import { buildGoldenThreadData } from '@/lib/studio/build-golden-thread-data';
import { CanvasView } from '@/components/canvas/canvas-view';
import { StudioPageHeader } from '@/components/ui/studio-page';

export const metadata: Metadata = {
  title: 'Data lineage | ALUCA Studio',
};

export const dynamic = 'force-dynamic';

export default async function CanvasPage() {
  const [lineage, goldenThread] = await Promise.all([
    buildLineageGraph(),
    buildGoldenThreadData(),
  ]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)', minHeight: 0, height: 'calc(100dvh - var(--shell-header) - 2 * var(--studio-page-gutter-y))' }}>
      <StudioPageHeader title="Data lineage" eyebrow="Assure" description="Trace source contracts through KPIs to use cases. Select an element to inspect its dependencies." compact />

      <Suspense
        fallback={
          <div className="h-[480px] rounded-lg border border-border bg-panel animate-pulse" />
        }
      >
        <CanvasView lineage={lineage} goldenThread={goldenThread} />
      </Suspense>
    </div>
  );
}
