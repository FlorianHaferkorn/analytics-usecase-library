/**
 * Plugin Loader — Loads plugin manifests from the filesystem.
 *
 * Scans the /plugins directory for manifest.json files and registers
 * valid plugins with the registry.
 */

import { readdirSync, readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import type { PluginManifest } from './plugin-types';

const PLUGINS_DIR = join(process.cwd(), 'plugins');

/** Validate a manifest has required fields. */
function isValidManifest(obj: unknown): obj is PluginManifest {
  if (!obj || typeof obj !== 'object') return false;
  const m = obj as Record<string, unknown>;
  return (
    typeof m.id === 'string' &&
    typeof m.name === 'string' &&
    typeof m.version === 'string' &&
    typeof m.author === 'string' &&
    typeof m.type === 'string' &&
    typeof m.description === 'string' &&
    typeof m.entrypoint === 'string' &&
    ['tool', 'widget', 'datasource'].includes(m.type as string)
  );
}

/** Load all plugin manifests from the /plugins directory. */
export function loadPluginManifests(): PluginManifest[] {
  if (!existsSync(PLUGINS_DIR)) return [];

  const manifests: PluginManifest[] = [];
  const entries = readdirSync(PLUGINS_DIR, { withFileTypes: true });

  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    const manifestPath = join(PLUGINS_DIR, entry.name, 'manifest.json');
    if (!existsSync(manifestPath)) continue;

    try {
      const raw = readFileSync(manifestPath, 'utf-8');
      const parsed = JSON.parse(raw);
      if (isValidManifest(parsed)) {
        manifests.push(parsed);
      } else {
        console.warn(`Skipping invalid plugin manifest: ${entry.name} — missing required fields`);
      }
    } catch (error) {
      console.warn(`Skipping plugin "${entry.name}":`, error instanceof Error ? error.message : error);
    }
  }

  return manifests;
}
