/**
 * Version Check — Detects duplicate plugin IDs with conflicting versions.
 */

import type { PluginManifest } from './plugin-types';

export interface VersionConflict {
  pluginId: string;
  versions: string[];
}

/**
 * Check an array of manifests for duplicate IDs with different versions.
 * Returns an array of conflicts (empty if none).
 */
export function checkVersionConflicts(manifests: PluginManifest[]): VersionConflict[] {
  const versionMap = new Map<string, Set<string>>();

  for (const m of manifests) {
    if (!versionMap.has(m.id)) {
      versionMap.set(m.id, new Set());
    }
    versionMap.get(m.id)!.add(m.version);
  }

  const conflicts: VersionConflict[] = [];
  for (const [pluginId, versions] of versionMap) {
    if (versions.size > 1) {
      conflicts.push({ pluginId, versions: Array.from(versions).sort() });
    }
  }

  return conflicts;
}
