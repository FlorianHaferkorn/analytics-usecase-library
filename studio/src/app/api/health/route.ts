/**
 * GET /api/health — runs tooling/health_scorecard.py --json and returns the result.
 */

import { execFileSync } from 'node:child_process';
import { join } from 'node:path';
import { apiSuccess, apiError } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';

export async function GET() {
  const repoRoot = join(process.cwd(), '..');
  try {
    const configuredPython = process.env.SUPERVERSION_PYTHON;
    const pythonExecutable = configuredPython || (process.platform === 'win32' ? 'py' : 'python3');
    const pythonArguments = [
      ...(process.platform === 'win32' && !configuredPython ? ['-3'] : []),
      'tooling/health_scorecard.py',
      '--json',
    ];
    const output = execFileSync(pythonExecutable, pythonArguments, {
      cwd: repoRoot,
      timeout: 30_000,
      encoding: 'utf-8',
    });
    const scorecard = JSON.parse(output) as unknown;
    return apiSuccess(scorecard);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return apiError(ErrorCode.INTERNAL_ERROR, `Health scorecard failed: ${message}`, 500);
  }
}
