import { Metadata } from 'next';
import { ReportTemplatesGallery } from '@/components/templates/report-templates-gallery';

export const metadata: Metadata = {
  title: 'Report Templates | Studio',
};

export default function TemplatesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-[28px] font-medium tracking-[-0.02em] text-foreground mb-1">
          Report Templates
        </h1>
        <p className="text-[13px] text-foreground-muted">
          T1–T4 gallery with design base (1280×720) and production preview (1920×1080). Tune theme
          in Tweaks and export Power BI / Evidence JSON.
        </p>
      </div>
      <ReportTemplatesGallery />
    </div>
  );
}
