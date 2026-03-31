/**
 * Type Generator: JSON Schema → TypeScript
 *
 * Reads all *.schema.json from tooling/ai/schemas/ and generates
 * corresponding TypeScript interfaces in studio/src/lib/schemas/.
 *
 * Run: npm run generate:types
 */

import { readdir, readFile, writeFile, mkdir } from 'node:fs/promises';
import { join, basename } from 'node:path';
import { compile } from 'json-schema-to-typescript';

const SCHEMA_DIR = join(import.meta.dirname, '..', '..', 'tooling', 'ai', 'schemas');
const OUTPUT_DIR = join(import.meta.dirname, '..', 'src', 'lib', 'schemas');

const BANNER = `/**
 * AUTO-GENERATED — DO NOT EDIT
 *
 * Generated from tooling/ai/schemas/ by scripts/generate-types.mjs
 * Re-generate with: npm run generate:types
 */\n\n`;

/** Convert schema filename to a clean TypeScript module name */
function toModuleName(filename) {
  return filename
    .replace('.schema.json', '')
    .replace(/_/g, '-')
    .toLowerCase();
}

async function main() {
  await mkdir(OUTPUT_DIR, { recursive: true });

  const files = (await readdir(SCHEMA_DIR)).filter((f) =>
    f.endsWith('.schema.json')
  );

  console.log(`Found ${files.length} schemas in ${SCHEMA_DIR}`);

  const exports = [];

  for (const file of files) {
    const schemaPath = join(SCHEMA_DIR, file);
    const raw = await readFile(schemaPath, 'utf-8');
    const schema = JSON.parse(raw);

    const moduleName = toModuleName(file);
    const outputPath = join(OUTPUT_DIR, `${moduleName}.ts`);

    try {
      // Ensure title is a valid TypeScript identifier
      let title = schema.title || moduleName;
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

      await writeFile(outputPath, BANNER + ts, 'utf-8');
      exports.push(moduleName);
      console.log(`  ✓ ${file} → ${moduleName}.ts`);
    } catch (err) {
      console.warn(`  ✗ ${file}: ${err.message}`);
    }
  }

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
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
