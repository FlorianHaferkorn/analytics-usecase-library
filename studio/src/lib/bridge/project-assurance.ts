/** Server-only adapter for the Python-owned delivery quality assessment. */
import 'server-only';

import { execFile } from 'node:child_process';
import { isAbsolute, join, resolve } from 'node:path';
import { readFile } from 'node:fs/promises';
import { loadProjectPackage, type PackageRepositoryResult } from '@/lib/bridge/project-package-repository';
import { withTemporaryDirectory, writePackageFiles } from '@/lib/project-package/package-files';

const REPO_ROOT_ENV = ['ALUCA', 'REPO', 'ROOT'].join('_');
const REPO_ROOT = process.env[REPO_ROOT_ENV]
  || (process.env.NODE_ENV === 'test' ? resolve(process.cwd(), '..') : undefined);
const PYTHON = process.env.SUPERVERSION_PYTHON || (process.platform === 'win32' ? 'py' : 'python3');
const PYTHON_ARGS = process.env.SUPERVERSION_PYTHON ? [] : process.platform === 'win32' ? ['-3'] : [];

export interface DeliveryQualityControl {
  id: string; title: string; requirement: string; gate: string; weight: number;
  status: 'passed' | 'gap'; evidence: string;
  source: { name: string; url: string; strength_adopted: string };
}
export interface DeliveryQualityAssessment {
  schema_version: string; project_ref: string; package_revision: number; weighted_score: number;
  score_interpretation: string;
  reference_review: { current: boolean; overdue_controls: string[]; next_due_at: string };
  gates: Record<string, { ready: boolean; blockers: string[] }>;
  dimensions: Array<{ id: string; title: string; intent: string; score: number; controls: DeliveryQualityControl[] }>;
}

function run(command: string[], cwd: string): Promise<void> {
  return new Promise((resolvePromise, reject) => {
    execFile(PYTHON, [...PYTHON_ARGS, ...command], { cwd, timeout: 60_000, maxBuffer: 8 * 1024 * 1024 }, (error) => {
      if (error && Number((error as NodeJS.ErrnoException).code) !== 2) reject(error); else resolvePromise();
    });
  });
}

export async function assessProjectDelivery(projectId: string, revision?: string): Promise<PackageRepositoryResult<DeliveryQualityAssessment>> {
  if (!REPO_ROOT) return { available: false, ok: false, error: 'Project assurance unavailable (ALUCA_REPO_ROOT not configured)' };
  const snapshot = await loadProjectPackage(projectId, revision);
  if (!snapshot.ok || !snapshot.value) return { ...snapshot, value: undefined };
  const packageSnapshot = snapshot.value;
  return withTemporaryDirectory('aluca-assurance-', async temporary => {
    const packageRoot = join(temporary, 'package');
    const output = join(temporary, 'assessment.json');
    try {
      await writePackageFiles(packageRoot, packageSnapshot.files);
      await run([
        '-m', 'tooling.superversion.project_package.delivery_quality',
        '--package', packageRoot,
        '--schemas', join(REPO_ROOT, 'tooling', 'generator', 'schemas'),
        '--model', join(REPO_ROOT, 'core', 'reference_models', 'e2e_delivery_quality', 'model.yaml'),
        '--output', output,
      ], isAbsolute(REPO_ROOT) ? REPO_ROOT : resolve(REPO_ROOT));
      const value = JSON.parse(await readFile(output, 'utf8')) as DeliveryQualityAssessment;
      if (value.project_ref !== projectId || value.package_revision !== packageSnapshot.revision.revision) {
        throw new Error('Assessment identity does not match the selected project revision');
      }
      return { available: true, ok: true, value };
    } catch (error) {
      return { available: true, ok: false, error: error instanceof Error ? error.message : 'Delivery assessment failed' };
    }
  });
}
