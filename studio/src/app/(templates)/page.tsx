import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Report Templates | Studio',
};

export default function TemplatesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Report Templates</h1>
        <p className="text-foreground-muted">T1-T4 page gallery with theme editor (Tweaks panel).</p>
      </div>

      <div className="grid grid-cols-1 gap-4">
        <div className="p-6 rounded-lg bg-panel border border-border">
          <h2 className="text-lg font-semibold text-foreground mb-4">T1 Strategic Overview</h2>
          <p className="text-foreground-muted text-sm">Phase 1 placeholder. Gallery and Tweaks panel in Phase 7.</p>
        </div>

        <div className="p-6 rounded-lg bg-panel border border-border">
          <h2 className="text-lg font-semibold text-foreground mb-4">T2 Tactical Variance</h2>
          <p className="text-foreground-muted text-sm">Phase 1 placeholder. Gallery and Tweaks panel in Phase 7.</p>
        </div>

        <div className="p-6 rounded-lg bg-panel border border-border">
          <h2 className="text-lg font-semibold text-foreground mb-4">T3 Operational Monitoring</h2>
          <p className="text-foreground-muted text-sm">Phase 1 placeholder. Gallery and Tweaks panel in Phase 7.</p>
        </div>

        <div className="p-6 rounded-lg bg-panel border border-border">
          <h2 className="text-lg font-semibold text-foreground mb-4">T4 Prescriptive Recommendation</h2>
          <p className="text-foreground-muted text-sm">Phase 1 placeholder. Gallery and Tweaks panel in Phase 7.</p>
        </div>
      </div>
    </div>
  );
}
