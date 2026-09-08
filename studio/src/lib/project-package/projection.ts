import { parse } from 'yaml';
import type { PackageSnapshot, PackageRevisionSummary } from '@/lib/bridge/project-package-repository';

export interface ProjectProjection {
  projectId: string;
  revision: PackageRevisionSummary;
  state: string;
  modules: Array<{ type: string; path: string; environment: string | null; data: Record<string, unknown> }>;
}

/** Read-only display projection. Validation/hashing remains Python repository-owned. */
export function projectProjection(projectId: string, snapshot: PackageSnapshot): ProjectProjection {
  if (snapshot.revision.project_ref !== projectId) throw new Error('Package project reference does not match the selected project');
  const read = (path: string): Record<string, unknown> => {
    const file = snapshot.files.find(item => item.path === path);
    if (!file) throw new Error(`Package module missing: ${path}`);
    const data: unknown = parse(Buffer.from(file.contentBase64, 'base64').toString('utf8'));
    if (!data || typeof data !== 'object' || Array.isArray(data)) throw new Error(`Invalid module object: ${path}`);
    return data as Record<string, unknown>;
  };
  const manifest = read('package.yaml');
  if (manifest.project_ref !== projectId || manifest.revision !== snapshot.revision.revision) throw new Error('Package manifest and revision metadata do not agree');
  if (!Array.isArray(manifest.modules)) throw new Error('Package modules unavailable');
  return {
    projectId, revision: snapshot.revision, state: String(manifest.state),
    modules: manifest.modules.map((entry: { module_type: string; path: string; environment?: string }) => ({
      type: entry.module_type, path: entry.path, environment: entry.environment ?? null, data: read(entry.path),
    })),
  };
}
