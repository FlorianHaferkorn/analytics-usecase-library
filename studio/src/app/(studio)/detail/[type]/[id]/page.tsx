import type { Metadata } from 'next';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { notFound } from 'next/navigation';
import { loadActionCode } from '@/lib/core/action-loader';
import { loadBracket, loadBracketYaml } from '@/lib/core/bracket-loader';
import { loadKpi } from '@/lib/core/catalog-loader';
import { loadContract } from '@/lib/core/contract-loader';
import { loadFactsheet, loadFactsheetMarkdown } from '@/lib/core/factsheet-loader';
import { DetailClient } from '@/components/detail/DetailClient';
import { UseCaseDetailClient } from '@/components/detail/UseCaseDetailClient';

interface DetailPageProps {
  params: Promise<{ type: string; id: string }>;
}

const BRACKET_SCHEMA_PATH = join(
  process.cwd(),
  '..',
  'tooling',
  'generator',
  'schemas',
  'usecase_bracket.schema.json',
);

async function loadBracketSchema(): Promise<Record<string, unknown> | undefined> {
  try {
    const raw = await readFile(BRACKET_SCHEMA_PATH, 'utf-8');
    return JSON.parse(raw) as Record<string, unknown>;
  } catch {
    return undefined;
  }
}

export async function generateMetadata({ params }: DetailPageProps): Promise<Metadata> {
  const { type, id } = await params;
  if (type === 'kpi') {
    const kpi = await loadKpi(id);
    if (kpi) return { title: `${kpi.kpi_key} | Studio` };
  }
  if (type === 'usecase') {
    const bracket = await loadBracket(id);
    if (bracket) return { title: `${bracket.title} | Studio` };
  }
  return { title: `${type}/${id} | Studio` };
}

export default async function DetailPage({ params }: DetailPageProps) {
  const { type, id } = await params;

  if (type === 'usecase') {
    const [bracket, yaml, markdown, factsheet, bracketSchema] = await Promise.all([
      loadBracket(id),
      loadBracketYaml(id),
      loadFactsheetMarkdown(id),
      loadFactsheet(id),
      loadBracketSchema(),
    ]);
    if (!bracket || !yaml || !markdown) notFound();
    return (
      <UseCaseDetailClient
        bracket={bracket}
        initialYaml={yaml}
        initialMarkdown={markdown}
        factsheet={factsheet}
        bracketSchema={bracketSchema}
      />
    );
  }

  if (type === 'kpi') {
    const kpi = await loadKpi(id);
    return <DetailClient kpi={kpi} type={type} id={id} />;
  }

  if (type === 'action') {
    const action = await loadActionCode(id);
    if (!action) notFound();
    return (
      <div className="space-y-2">
        <h1 className="text-2xl font-medium text-foreground">{action.name}</h1>
        <p className="text-foreground-muted text-sm font-mono">{action.id}</p>
        <p className="text-foreground-muted text-sm">Full action playbook editor — Epic 3+.</p>
      </div>
    );
  }

  if (type === 'contract') {
    const contract = await loadContract(id);
    if (!contract) notFound();
    return (
      <div className="space-y-2">
        <h1 className="text-2xl font-medium text-foreground">{contract.domain}</h1>
        <p className="text-foreground-muted text-sm">Owner: {contract.owner}</p>
        <p className="text-foreground-muted text-sm">Contract YAML editor — Epic 3+.</p>
      </div>
    );
  }

  notFound();
}
