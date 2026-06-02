'use client';

import { useEffect, useRef, useState } from 'react';
import { PageTemplatePreview, type PageTemplateId } from '@/components/templates/page-template-preview';
import { ThemeExportPanel } from '@/components/brand/theme-export-panel';
import { TweaksTab } from '@/components/brand/tweaks-tab';
import { useProjectStore, DEFAULT_THEME } from '@/lib/store/project-store';

const TEMPLATES: Array<{
  id: PageTemplateId;
  title: string;
  decision: string;
  slots: string;
  pageKind: string;
}> = [
  {
    id: 'T1',
    title: 'T1 Strategic Overview',
    pageKind: 'Overview · 3s + 30s',
    decision: 'Are we on track against plan?',
    slots: 'Zone 1: KPI band · Zone 2: slicers · Zone 3: trend · variance · mix',
  },
  {
    id: 'T2',
    title: 'T2 Tactical Variance',
    pageKind: 'Overview · 3s + 30s',
    decision: 'Where did we miss vs plan and why?',
    slots: 'Zone 1: variance KPIs · Zone 2: slicers · Zone 3: trend · bridge · drivers',
  },
  {
    id: 'T3',
    title: 'T3 Operational Monitoring',
    pageKind: 'Overview · exceptions',
    decision: 'Which entities need intervention today?',
    slots: 'Zone 1: exception counts · Zone 3: severity-sorted list · spark',
  },
  {
    id: 'T4',
    title: 'T4 Prescriptive Recommendation',
    pageKind: 'Detail · 300s',
    decision: 'What action, for which entity, with what impact?',
    slots: 'Slicer pane · narrative · detail matrix · action panel',
  },
];

/** Design-base canvas per `core/templates/page_templates/tokens/layout_grid.yaml`. */
export const DESIGN_CANVAS = { w: 1280, h: 720 } as const;

/** Production canvas per bracket `report_canvas` / Power BI connector. */
export const PRODUCTION_CANVAS = { w: 1920, h: 1080 } as const;

type CanvasView = 'design' | 'production';

const CANVAS_BY_VIEW: Record<CanvasView, { w: number; h: number; shortLabel: string; hint: string }> = {
  design: {
    w: DESIGN_CANVAS.w,
    h: DESIGN_CANVAS.h,
    shortLabel: 'Design base',
    hint: '12×12 LU grid · slot coordinates in page specs',
  },
  production: {
    w: PRODUCTION_CANVAS.w,
    h: PRODUCTION_CANVAS.h,
    shortLabel: 'Production',
    hint: 'Fabric / PBIP export size · typography scales per connector',
  },
};

export function ReportTemplatesGallery() {
  const theme = useProjectStore((s) => s.theme);
  const setTheme = useProjectStore((s) => s.setTheme);
  const [activeId, setActiveId] = useState<string>(TEMPLATES[0]!.id);
  const [annotate, setAnnotate] = useState(true);
  const [canvasView, setCanvasView] = useState<CanvasView>('design');
  const [saving, setSaving] = useState(false);
  const [fitScale, setFitScale] = useState(1);
  const viewportRef = useRef<HTMLDivElement>(null);

  const active = TEMPLATES.find((t) => t.id === activeId) ?? TEMPLATES[0]!;
  const canvas = CANVAS_BY_VIEW[canvasView];

  useEffect(() => {
    const el = viewportRef.current;
    if (!el) return;

    const updateScale = () => {
      const horizontalPad = 32;
      const available = Math.max(200, el.clientWidth - horizontalPad);
      setFitScale(Math.min(1, available / canvas.w));
    };

    updateScale();
    const ro = new ResizeObserver(updateScale);
    ro.observe(el);
    return () => ro.disconnect();
  }, [canvas.w, canvasView]);

  const handleSaveTheme = async () => {
    setSaving(true);
    try {
      await fetch('/api/theme', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ projectId: 'default', theme }),
      });
    } finally {
      setSaving(false);
    }
  };

  const scaledW = canvas.w * fitScale;
  const scaledH = canvas.h * fitScale;

  return (
    <div className="flex flex-col lg:flex-row gap-6 min-h-0">
      <div className="flex-1 min-w-0 space-y-4">
        <p className="text-[12px] text-foreground-muted">
          Design base {DESIGN_CANVAS.w}×{DESIGN_CANVAS.h} · Production {PRODUCTION_CANVAS.w}×
          {PRODUCTION_CANVAS.h}
        </p>

        <div className="flex flex-wrap items-center gap-3">
          {TEMPLATES.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setActiveId(t.id)}
              className={`px-3 py-1.5 rounded-lg text-[13px] border transition-colors ${
                activeId === t.id
                  ? 'bg-foreground text-background border-foreground font-medium'
                  : 'bg-panel text-foreground-muted border-border hover:bg-hover'
              }`}
            >
              {t.id}
            </button>
          ))}

          <div
            className="flex rounded-lg border border-border overflow-hidden"
            role="group"
            aria-label="Canvas size"
          >
            {(['design', 'production'] as const).map((mode) => (
              <button
                key={mode}
                type="button"
                onClick={() => setCanvasView(mode)}
                className={`px-3 py-1.5 text-[12px] transition-colors ${
                  canvasView === mode
                    ? 'bg-foreground text-background font-medium'
                    : 'bg-panel text-foreground-muted hover:bg-hover'
                }`}
              >
                {CANVAS_BY_VIEW[mode].shortLabel}
              </button>
            ))}
          </div>

          <label className="ml-auto flex items-center gap-2 text-[13px] text-foreground-muted cursor-pointer">
            <input
              type="checkbox"
              checked={annotate}
              onChange={(e) => setAnnotate(e.target.checked)}
            />
            Slot annotations
          </label>
        </div>

        <div className="rounded-lg border border-border bg-panel overflow-hidden">
          <div className="px-4 py-3 border-b border-border flex justify-between items-start gap-4">
            <div>
              <h2 className="text-base font-medium text-foreground">{active.title}</h2>
              <p className="text-[12px] text-foreground-muted mt-1">{active.decision}</p>
              <p className="text-[11px] text-foreground-subtle mt-1">{canvas.hint}</p>
              {annotate && (
                <p className="text-[11px] font-mono text-accent mt-2">{active.slots}</p>
              )}
            </div>
            <div className="text-right shrink-0">
              <span className="text-[11px] font-mono text-foreground block">
                {canvas.w}×{canvas.h}
              </span>
              {fitScale < 1 && (
                <span className="text-[10px] text-foreground-subtle">
                  fit {Math.round(fitScale * 100)}%
                </span>
              )}
            </div>
          </div>

          <div
            ref={viewportRef}
            className="relative bg-background overflow-hidden flex justify-center items-start p-4"
            style={{ minHeight: scaledH + 32 }}
          >
            <div
              style={{
                width: scaledW,
                height: scaledH,
              }}
            >
              <div
                className="border border-border rounded-lg overflow-hidden shadow-sm origin-top-left"
                style={{
                  width: canvas.w,
                  height: canvas.h,
                  transform: `scale(${fitScale})`,
                }}
              >
                <PageTemplatePreview templateId={active.id as PageTemplateId} theme={theme} />
              </div>
            </div>
          </div>

          {canvasView === 'production' && (
            <p className="px-4 py-2 text-[11px] text-foreground-subtle border-t border-border bg-bg-2">
              Production view uses the Fabric canvas size. Final typography follows the Power BI
              connector (+2pt at 1920×1080). Wireframe follows page-type zones (3s/30s/300s); exact
              12×12 LU positions come with slot-accurate mockup port.
            </p>
          )}
        </div>
      </div>

      <aside className="w-full lg:w-[320px] shrink-0 space-y-4">
        <div className="rounded-lg border border-border bg-panel p-4">
          <h3 className="text-sm font-medium text-foreground mb-3">Tweaks</h3>
          <TweaksTab theme={theme} onUpdate={setTheme} onSave={handleSaveTheme} saving={saving} />
        </div>
        <ThemeExportPanel theme={theme} onSave={handleSaveTheme} saving={saving} />
        <button
          type="button"
          onClick={() => setTheme(DEFAULT_THEME)}
          className="w-full text-[12px] text-foreground-muted hover:text-foreground py-2"
        >
          Reset to Aurora default
        </button>
      </aside>
    </div>
  );
}
