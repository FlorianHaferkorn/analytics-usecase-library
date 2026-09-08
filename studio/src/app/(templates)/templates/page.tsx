import { Metadata } from 'next';
import { ReportTemplatesGallery } from '@/components/templates/report-templates-gallery';
import { StudioPage, StudioPageHeader } from '@/components/ui/studio-page';

export const metadata: Metadata = {
  title: 'Report Templates | Studio',
};

export default function TemplatesPage() {
  return (
    <StudioPage width="wide">
      <StudioPageHeader
        eyebrow="Assets / Brand & Templates"
        title="Report Templates"
        description="Review T1–T4 decision layouts at their governed design and production sizes, then export the same theme contract to Power BI or Evidence."
        badge="4 governed layouts"
        tone="info"
      />
      <ReportTemplatesGallery />
    </StudioPage>
  );
}
