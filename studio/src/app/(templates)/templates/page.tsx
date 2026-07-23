import { Metadata } from 'next';
import { TemplatesClient } from './templates-client';

export const metadata: Metadata = {
  title: 'Report Templates | Studio',
};

export default function TemplatesPage() {
  return <TemplatesClient />;
}
