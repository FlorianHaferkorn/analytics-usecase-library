import { Metadata } from 'next';
import { Suspense } from 'react';
import { buildLineageGraph } from '@/lib/core/lineage-builder';
import { buildGoldenThreadData } from '@/lib/studio/build-golden-thread-data';
import { CanvasView } from '@/components/canvas/canvas-view';

export const metadata: Metadata = {
  title: 'Canvas | Studio',
};

export const dynamic = 'force-dynamic';

export default async function CanvasPage() {
  const [lineage, goldenThread] = await Promise.all([
    buildLineageGraph(),
    buildGoldenThreadData(),
  ]);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-[28px] font-medium tracking-[-0.02em] text-foreground mb-1">
          Canvas
        </h1>
        <p className="text-[13px] text-foreground-muted">
          Data lineage and Golden Thread — pan, zoom, open entities in Detail.
        </p>
      </div>

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
