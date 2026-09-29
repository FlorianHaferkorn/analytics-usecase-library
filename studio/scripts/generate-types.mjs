/**
 * Type Generator: JSON Schema → TypeScript
 *
 * Reads *.schema.json from tooling/generator/schemas/ (the schema authority, AGENTS.md) and
 * generates corresponding TypeScript interfaces in studio/src/lib/schemas/.
 *
 * Run: npm run generate:types                              (regenerates the generated set)
 *      npm run generate:types -- data_contract.schema.json  (only the named schema(s))
 *
 * The generated set is every module in src/lib/schemas/ that carries the AUTO-GENERATED banner.
 * Until 29.09.2026 the script read tooling/ai/schemas/, which no longer exists; the schema
 * directory holds ~47 schemas, most without a Studio consumer, so "all of them" is no longer
 * the default. A new schema joins the set by naming it once.
 */

import { readdir, readFile, writeFile, mkdir } from 'node:fs/promises';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { compile } from 'json-schema-to-typescript';

export const SCHEMA_DIR = join(import.meta.dirname, '..', '..', 'tooling', 'generator', 'schemas');
export const OUTPUT_DIR = join(import.meta.dirname, '..', 'src', 'lib', 'schemas');

const BANNER = `/**
 * AUTO-GENERATED — DO NOT EDIT
 *
 * Generated from tooling/generator/schemas/ by scripts/generate-types.mjs
 * Re-generate with: npm run generate:types
 */\n\n`;

/** Convert schema filename to a clean TypeScript module name */
export function toModuleName(filename) {
  return filename
    .replace('.schema.json', '')
    .replace(/_/g, '-')
    .toLowerCase();
}

/** Module names (without .ts) in OUTPUT_DIR that carry the AUTO-GENERATED banner. */
export async function generatedModules() {
  const names = [];
  for (const f of await readdir(OUTPUT_DIR)) {
    if (!f.endsWith('.ts') || f === 'index.ts') continue;
    const head = (await readFile(join(OUTPUT_DIR, f), 'utf-8')).slice(0, 200);
    if (head.includes('AUTO-GENERATED')) names.push(f.replace(/\.ts$/, ''));
  }
  return names;
}

/** The TypeScript module text for one schema file (banner included), as written to OUTPUT_DIR. */
export async function renderModule(file) {
  const schema = JSON.parse(await readFile(join(SCHEMA_DIR, file), 'utf-8'));
  // Ensure title is a valid TypeScript identifier
  let title = schema.title || toModuleName(file);
  if (/^\d/.test(title.replace(/[^a-zA-Z0-9]/g, ''))) {
    title = 'Layout' + title.replace(/[^a-zA-Z0-9]/g, '');
  }
  // Also patch the schema title so internal refs use the clean name
  const patchedSchema = { ...schema, title };
  const ts = await compile(patchedSchema, title, {
    bannerComment: '',
    additionalProperties: false,
    strictIndexSignatures: true,
    style: { semi: true, singleQuote: true },
  });
  return BANNER + ts;
}

async function main() {
  await mkdir(OUTPUT_DIR, { recursive: true });

  const available = (await readdir(SCHEMA_DIR)).filter((f) =>
    f.endsWith('.schema.json')
  );
  const requested = process.argv.slice(2);
  const existing = new Set(await generatedModules());
  const files = requested.length
    ? requested
    : available.filter((f) => existing.has(toModuleName(f)));
  const missing = files.filter((f) => !available.includes(f));
  if (missing.length) {
    throw new Error(`Not in ${SCHEMA_DIR}: ${missing.join(', ')}`);
  }

  console.log(`Generating ${files.length} of ${available.length} schemas in ${SCHEMA_DIR}`);

  let failed = 0;

  for (const file of files) {
    const moduleName = toModuleName(file);
    const outputPath = join(OUTPUT_DIR, `${moduleName}.ts`);

    try {
      await writeFile(outputPath, await renderModule(file), 'utf-8');
      console.log(`  ✓ ${file} → ${moduleName}.ts`);
    } catch (err) {
      failed += 1;
      console.warn(`  ✗ ${file}: ${err.message}`);
    }
  }

  const exports = await generatedModules();

  // Generate barrel export
  const barrelContent =
    BANNER +
    exports
      .map((name) => `export * from './${name}';`)
      .sort()
      .join('\n') +
    '\n';

  await writeFile(join(OUTPUT_DIR, 'index.ts'), barrelContent, 'utf-8');
  console.log(`\nGenerated index.ts with ${exports.length} exports`);
  if (failed) process.exit(1);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((err) => {
    console.error(err);
    process.exit(1);
  });
}
