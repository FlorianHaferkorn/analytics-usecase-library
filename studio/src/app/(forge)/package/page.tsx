import type { Metadata } from 'next';
import { ProjectPackageClient } from '@/app/(studio)/package/project-package-client';

export const metadata: Metadata = {
  title: 'Project Package | Studio',
};

export default function ProjectPackagePage() {
  return <ProjectPackageClient />;
}
