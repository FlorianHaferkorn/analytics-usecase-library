/**
 * Org Role Loader
 *
 * Loads org_roles.yaml from core/organization/ and returns typed ResolvedRole
 * objects with computed avatar initials and deterministic hue. Server-side only.
 */

import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { parseYaml } from './yaml-loader';
import type { OrgRegistryV10 } from '@/lib/schemas/org-roles';

const ORG_ROLES_PATH = join(
  process.cwd(),
  '..',
  'core',
  'organization',
  'org_roles.yaml'
);

export interface ResolvedRole {
  id: string;
  title: string;
  domain: string;
  avatar_initials: string; // first letter of first two words
  hue: number;             // deterministic 0-360 from djb2 hash of title
}

/** djb2 hash — returns a positive integer. */
function hashString(s: string): number {
  let h = 5381;
  for (let i = 0; i < s.length; i++) {
    h = ((h << 5) + h) ^ s.charCodeAt(i);
    h = h >>> 0; // keep unsigned 32-bit
  }
  return h;
}

/** Derive initials from a title: first letter of the first two words. */
function avatarInitials(title: string): string {
  const words = title
    .replace(/[/&]/g, ' ')   // treat slashes and ampersands as word separators
    .split(/\s+/)
    .filter((w) => w.length > 0);
  return words
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join('');
}

/** Resolve a single raw role entry into a ResolvedRole. */
function resolveEntry(role: { id: string; title: string; domain: string }): ResolvedRole {
  return {
    id: role.id,
    title: role.title,
    domain: role.domain,
    avatar_initials: avatarInitials(role.title),
    hue: hashString(role.title) % 360,
  };
}

// Module-level cache — lives for the lifetime of the server process (build-time safe).
let _cache: Map<string, ResolvedRole> | null = null;

/** Load all org roles as a Map keyed by id. Results are cached in-process. */
export async function loadOrgRoles(): Promise<Map<string, ResolvedRole>> {
  if (_cache) return _cache;

  const raw = await readFile(ORG_ROLES_PATH, 'utf-8');
  const registry = parseYaml<OrgRegistryV10>(raw);

  const map = new Map<string, ResolvedRole>();
  for (const role of registry.roles) {
    map.set(role.id, resolveEntry(role));
  }

  _cache = map;
  return map;
}

/** Resolve a single role id to a ResolvedRole, or null if not found. */
export async function resolveRole(id: string): Promise<ResolvedRole | null> {
  const map = await loadOrgRoles();
  return map.get(id) ?? null;
}
