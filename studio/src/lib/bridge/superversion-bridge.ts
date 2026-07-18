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

export interface GateStage {
  name: string;
  status: 'PASS' | 'FAIL' | 'SKIP';
  detail: string;
}

export interface GateReport {
  ok: boolean;
  stages: GateStage[];
}

export interface GenerateArtifact {
  path: string;
  bytes: number;
}

/** Result of the "Nach dem Core" generate step (I-6.3). */
export interface GenerateResult {
  available: boolean;
  ok: boolean;
  bracket?: string;
  target?: string;
  targetLabel?: string;
  targetStatus?: string;
  targetsAvailable: string[];
  artifacts: GenerateArtifact[];
  gate?: GateReport;
  error?: string;
}

interface GeneratePayload {
  ok: boolean;
  bracket?: string;
  target?: string;
  target_label?: string;
  target_status?: string;
  targets_available?: string[];
  artifacts?: GenerateArtifact[];
  gate?: GateReport;
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

function toGenerateResult(payload: GeneratePayload): GenerateResult {
  return {
    available: true,
    ok: payload.ok,
    bracket: payload.bracket,
    target: payload.target,
    targetLabel: payload.target_label,
    targetStatus: payload.target_status,
    targetsAvailable: payload.targets_available ?? [],
    artifacts: payload.artifacts ?? [],
    gate: payload.gate,
    error: payload.error,
  };
}

export interface BridgePing {
  available: boolean;
  enginesAvailable: string[];
  targetsAvailable: string[];
  error?: string;
}

/** Cheap readiness probe for the Python bridge (I-6.5) — no model work. */
export async function pingBridge(): Promise<BridgePing> {
  try {
    const payload = JSON.parse(
      await spawnBridge(['-m', 'tooling.superversion.bridge', 'ping']),
    ) as { ok: boolean; engines_available?: string[]; targets_available?: string[] };
    return {
      available: payload.ok === true,
      enginesAvailable: payload.engines_available ?? [],
      targetsAvailable: payload.targets_available ?? [],
    };
  } catch (err) {
    const e = err as ExecError;
    return {
      available: false,
      enginesAvailable: [],
      targetsAvailable: [],
      error: e.code === 'ENOENT' ? `Python bridge unavailable (${PYTHON} not found)` : e.message || 'bridge error',
    };
  }
}

export interface AttributionRecord {
  actionCodeId: string;
  kpiId: string;
  method: 'before_after' | 'diff_in_diff' | 'holdout';
  status: 'computed' | 'uncomputed';
  t0: number | null;
  t1: number | null;
  delta: number | null;
  note: string;
}

export interface RefinementProposal {
  actionCodeId: string;
  kpiId: string;
  trigger: 'no_effect' | 'material_effect';
  relChange: number;
  rationale: string;
  status: 'pending_review';
}

/** Result of the "attribute" step (I-8.2/I-8.3, ADR-0009 §5, Studio-Approval-Verdrahtung). */
export interface AttributeResult {
  available: boolean;
  ok: boolean;
  useCase?: string;
  actionCodeId?: string;
  method?: string;
  outcomeKpis: string[];
  attribution: AttributionRecord[];
  refinements: RefinementProposal[];
  error?: string;
}

interface AttributePayload {
  ok: boolean;
  use_case?: string;
  action_code_id?: string;
  method?: string;
  outcome_kpis?: string[];
  attribution?: Array<{
    action_code_id: string; kpi_id: string; method: string; status: string;
    t0: number | null; t1: number | null; delta: number | null; note: string;
  }>;
  refinements?: Array<{
    action_code_id: string; kpi_id: string; trigger: string; rel_change: number;
    rationale: string; status: string;
  }>;
  error?: string;
}

function toAttributeResult(payload: AttributePayload): AttributeResult {
  return {
    available: true,
    ok: payload.ok,
    useCase: payload.use_case,
    actionCodeId: payload.action_code_id,
    method: payload.method,
    outcomeKpis: payload.outcome_kpis ?? [],
    attribution: (payload.attribution ?? []).map((r) => ({
      actionCodeId: r.action_code_id,
      kpiId: r.kpi_id,
      method: r.method as AttributionRecord['method'],
      status: r.status as AttributionRecord['status'],
      t0: r.t0,
      t1: r.t1,
      delta: r.delta,
      note: r.note,
    })),
    refinements: (payload.refinements ?? []).map((p) => ({
      actionCodeId: p.action_code_id,
      kpiId: p.kpi_id,
      trigger: p.trigger as RefinementProposal['trigger'],
      relChange: p.rel_change,
      rationale: p.rationale,
      status: 'pending_review',
    })),
    error: payload.error,
  };
}

/**
 * Attribute an action's KPI effect via the Python bridge: governed refcalc
 * baseline (t0) + caller-supplied after-values (t1), plus derived, reviewable
 * refinement proposals (I-8.2/I-8.3, ADR-0009 §5). Never auto-applies anything —
 * proposals carry `status: 'pending_review'` for Studio's approval gate.
 */
export async function runAttribute(
  useCase: string,
  actionCodeId: string,
  t1: Record<string, number>,
  opts?: { method?: 'before_after' | 'diff_in_diff' | 'holdout'; controlT0?: Record<string, number>; controlT1?: Record<string, number> },
): Promise<AttributeResult> {
  const args = [
    '-m', 'tooling.superversion.bridge', 'attribute', useCase, actionCodeId,
    '--t1', JSON.stringify(t1),
  ];
  if (opts?.method) args.push('--method', opts.method);
  if (opts?.controlT0) args.push('--control-t0', JSON.stringify(opts.controlT0));
  if (opts?.controlT1) args.push('--control-t1', JSON.stringify(opts.controlT1));

  try {
    return toAttributeResult(JSON.parse(await spawnBridge(args)) as AttributePayload);
  } catch (err) {
    const e = err as ExecError;
    if (e.stdout) {
      try {
        return toAttributeResult(JSON.parse(e.stdout) as AttributePayload);
      } catch {
        /* not our JSON — fall through to transport-unavailable */
      }
    }
    return {
      available: false,
      ok: false,
      outcomeKpis: [],
      attribution: [],
      refinements: [],
      error:
        e.code === 'ENOENT'
          ? `Python bridge unavailable (${PYTHON} not found)`
          : e.message || 'bridge error',
    };
  }
}

/**
 * Emit a target + Gate-Report for a bracket via the Python bridge (I-6.3).
 * `available: false` is a transport failure; `ok` otherwise mirrors the gate.
 */
export async function runGenerate(bracketId: string, target = 'tmdl'): Promise<GenerateResult> {
  const bracketPath = await resolveBracketPath(bracketId);
  if (!bracketPath) {
    return { available: true, ok: false, targetsAvailable: [], artifacts: [], error: `Bracket not found: ${bracketId}` };
  }

  const args = ['-m', 'tooling.superversion.bridge', 'generate', bracketPath, '--target', target];
  try {
    return toGenerateResult(JSON.parse(await spawnBridge(args)) as GeneratePayload);
  } catch (err) {
    const e = err as ExecError;
    if (e.stdout) {
      try {
        return toGenerateResult(JSON.parse(e.stdout) as GeneratePayload);
      } catch {
        /* not our JSON — fall through to transport-unavailable */
      }
    }
    return {
      available: false,
      ok: false,
      targetsAvailable: [],
      artifacts: [],
      error:
        e.code === 'ENOENT'
          ? `Python bridge unavailable (${PYTHON} not found)`
          : e.message || 'bridge error',
    };
  }
}
