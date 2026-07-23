'use client';

import Link from 'next/link';
import { StudioPage, StudioPageHeader } from '@/components/ui/studio-page';

export function DetailEntityStub({
  eyebrow,
  title,
  subtitle,
  description,
  backHref = '/library',
  backLabel = 'Back to library',
}: {
  eyebrow: string;
  title: string;
  subtitle?: string;
  description: string;
  backHref?: string;
  backLabel?: string;
}) {
  return (
    <StudioPage>
      <StudioPageHeader
        eyebrow={eyebrow}
        title={title}
        description={description}
        badge={subtitle}
        tone="info"
        actions={
          <Link href={backHref} style={{ fontSize: 13, color: 'var(--accent)', textDecoration: 'none' }}>
            ← {backLabel}
          </Link>
        }
      />
    </StudioPage>
  );
}
