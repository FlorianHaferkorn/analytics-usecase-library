import type { Metadata } from 'next';

interface DetailPageProps {
  params: Promise<{
    type: string;
    id: string;
  }>;
}

export async function generateMetadata({ params }: DetailPageProps): Promise<Metadata> {
  const { type, id } = await params;
  return {
    title: `Detail: ${type}/${id} | Studio`,
  };
}

export default async function DetailPage({ params }: DetailPageProps) {
  const { type, id } = await params;
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Detail</h1>
        <p className="text-foreground-muted">Entity editing surface: Factsheet, Bracket, Data Contracts, History.</p>
        <p className="text-foreground-subtle text-sm mt-2">
          Type: {type} | ID: {id}
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4">
        <div className="p-6 rounded-lg bg-panel border border-border">
          <h2 className="text-lg font-semibold text-foreground mb-4">Tabs (Factsheet, Bracket, etc.)</h2>
          <p className="text-foreground-muted text-sm">
            Phase 1 placeholder. Tab UI and Cascading AI wiring in Phase 3.
          </p>
        </div>
      </div>
    </div>
  );
}
