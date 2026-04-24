import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Canvas | Studio',
};

export default function CanvasPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Canvas</h1>
        <p className="text-foreground-muted">Golden Thread lineage graph.</p>
      </div>

      <div className="grid grid-cols-1 gap-4">
        <div className="p-6 rounded-lg bg-panel border border-border">
          <h2 className="text-lg font-semibold text-foreground mb-4">Lineage Graph</h2>
          <p className="text-foreground-muted text-sm">
            Phase 1 placeholder. Data wiring in Phase 4.
          </p>
        </div>
      </div>
    </div>
  );
}
