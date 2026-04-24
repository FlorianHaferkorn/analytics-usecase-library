import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Library | Studio',
};

export default function LibraryPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Library</h1>
        <p className="text-foreground-muted">Browse all entities: KPIs, Data Sources, Action Codes, Use Cases.</p>
      </div>

      <div className="grid grid-cols-1 gap-4">
        <div className="p-6 rounded-lg bg-panel border border-border">
          <h2 className="text-lg font-semibold text-foreground mb-4">Entity Registry</h2>
          <p className="text-foreground-muted text-sm">
            Phase 1 placeholder. Tab UI and data wiring in Phase 2.
          </p>
        </div>
      </div>
    </div>
  );
}
