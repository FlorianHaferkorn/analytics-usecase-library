import { notFound } from 'next/navigation';
import { loadBracket } from '@/lib/core/bracket-loader';
import { loadFactsheet } from '@/lib/core/factsheet-loader';
import { resolveRole } from '@/lib/core/org-role-loader';
import { loadAllSpines } from '@/lib/core/spine-loader';
import { BracketDetail } from '@/components/brackets/bracket-detail';

export default async function BracketDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const [bracket, factsheet, spines] = await Promise.all([
    loadBracket(id).catch(() => null),
    loadFactsheet(id).catch(() => null),
    loadAllSpines().catch(() => []),
  ]);
  if (!bracket) notFound();

  const [ownerRole, stewardRole] = await Promise.all([
    resolveRole(bracket.governance.owner_role).catch(() => null),
    resolveRole(bracket.governance.steward_role).catch(() => null),
  ]);

  return (
    <BracketDetail
      bracket={bracket}
      factsheet={factsheet}
      ownerRole={ownerRole}
      stewardRole={stewardRole}
      spines={spines}
    />
  );
}
