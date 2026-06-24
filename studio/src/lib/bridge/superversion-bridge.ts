/**
 * Superversion bridge — the Studio→Python seam (ADR-0007, subprocess transport).
 *
 * The Studio docks onto the governed Python Superversion by spawning its bridge
 * module and reading JSON from stdout (decision E-1, transport ratified
 * 2026-06-24). No Python lives in the Studio — this only spawns
 * `tooling/superversion/bridge.py`, which owns the generation truth.
 *
 * Server-side only (uses node:child_process). Honest degradation (ADR-0007
 * rule 5): if the bridge cannot run, `available` is false and the caller shows a
 * "not gate-validated" state — never a fabricated green result.
 */

import { execFile } from 'node:child_process';
import { join } from 'node:path';
import { resolveBracketPath } from '@/lib/core/bracket-loader';

/** Repo root, relative to the Studio cwd — where `python -m tooling.superversion...` resolves. */
const REPO_ROOT = join(process.cwd(), '..');
const PYTHON = process.env.SUPERVERSION_PYTHON || 'python3';

export interface PreCoreFinding {
  severity: 'info' | 'warn' | 'error';
  code: string;
  detail: string;
}

export interface PreCoreEngine {
  id: string;
  label: string;
  status: string;
  ok: boolean;
  counts: Record<string, number>;
  findings: PreCoreFinding[];
}

/** Result of the "Vor dem Core" reality check (I-6.2). */
export interface PreCoreResult {
  /** false → the Python bridge could not run (transport down); show honest banner. */
  available: boolean;
  /** the core's verdict (only meaningful when available). */
  ok: boolean;
  bracket?: string;
  engines: PreCoreEngine[];
  error?: string;
}

interface BridgePayload {
  ok: boolean;
  bracket?: string;
  engines?: PreCoreEngine[];
  error?: string;
}

type ExecError = Error & { code?: string | number; stdout?: string };

/** Spawn the bridge and resolve its stdout; reject (with stdout attached) on non-zero exit. */
function spawnBridge(args: string[]): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile(
      PYTHON,
      args,
      { cwd: REPO_ROOT, timeout: 30_000, maxBuffer: 8 * 1024 * 1024 },
      (err, stdout) => {
        if (err) {
          (err as ExecError).stdout = stdout;
          reject(err);
        } else {
          resolve(stdout);
        }
      },
    );
  });
}

function toResult(payload: BridgePayload): PreCoreResult {
  return {
    available: true,
    ok: payload.ok,
    bracket: payload.bracket,
    engines: payload.engines ?? [],
    error: payload.error,
  };
}

/**
 * Run the gov/eng/arch engines against a bracket via the Python bridge.
 * Distinguishes a core verdict (`available: true`, `ok` reflects findings) from a
 * transport failure (`available: false`).
 */
export async function runPreCore(bracketId: string): Promise<PreCoreResult> {
  const bracketPath = await resolveBracketPath(bracketId);
  if (!bracketPath) {
    return { available: true, ok: false, engines: [], error: `Bracket not found: ${bracketId}` };
  }

  const args = ['-m', 'tooling.superversion.bridge', 'precore', bracketPath];
  try {
    return toResult(JSON.parse(await spawnBridge(args)) as BridgePayload);
  } catch (err) {
    const e = err as ExecError;
    // A non-zero exit still carries our JSON error on stdout — that's a core verdict.
    if (e.stdout) {
      try {
        return toResult(JSON.parse(e.stdout) as BridgePayload);
      } catch {
        /* not our JSON — fall through to transport-unavailable */
      }
    }
    return {
      available: false,
      ok: false,
      engines: [],
      error:
        e.code === 'ENOENT'
          ? `Python bridge unavailable (${PYTHON} not found)`
          : e.message || 'bridge error',
    };
  }
}
