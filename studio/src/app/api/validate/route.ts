import { NextResponse } from 'next/server';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { validate } from '@/lib/validation/schema-validator';

const SCHEMA_DIR = join(process.cwd(), '..', 'tooling', 'ai', 'schemas');

const SCHEMA_MAP: Record<string, string> = {
  bracket: 'usecase_bracket.schema.json',
  action: 'action_code.schema.json',
  kpi: 'kpi_definition.schema.json',
  contract: 'data_contract.schema.json',
  layout: 'layout_330300.schema.json',
};

export async function POST(request: Request) {
  const body = await request.json();
  const { schemaType, data } = body as { schemaType: string; data: unknown };

  const schemaFile = SCHEMA_MAP[schemaType];
  if (!schemaFile) {
    return NextResponse.json(
      { error: `Unknown schema type: ${schemaType}. Valid: ${Object.keys(SCHEMA_MAP).join(', ')}` },
      { status: 400 }
    );
  }

  const schemaPath = join(SCHEMA_DIR, schemaFile);
  const raw = await readFile(schemaPath, 'utf-8');
  const schema = JSON.parse(raw);

  const result = validate(schema, data);

  return NextResponse.json(result);
}
