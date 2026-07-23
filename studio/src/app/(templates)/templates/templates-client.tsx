'use client';

import { ReportTemplatesGallery } from '@/components/templates/report-templates-gallery';
import { StudioPage, StudioPageHeader } from '@/components/ui/studio-page';

export function TemplatesClient() {
  return (
    <StudioPage>
      <StudioPageHeader
        eyebrow="Forge / Templates"
        title="Report Templates"
        description="T1–T4 gallery with design base (1280×720) and production preview (1920×1080). Tune theme in Tweaks and export Power BI / Evidence JSON."
        badge="T1–T4"
        tone="info"
      />
      <ReportTemplatesGallery />
    </StudioPage>
  );
}
