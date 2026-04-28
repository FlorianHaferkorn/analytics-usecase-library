import { permanentRedirect } from 'next/navigation';

/** Legacy redirect — Dashboard was renamed to Overview. */
export default function DashboardLegacyPage() {
  permanentRedirect('/overview');
}
