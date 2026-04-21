/**
 * Adapter<IR, Output> — universal interface for export adapters.
 *
 * Every connector (Fabric, OSS, CICD, Grafana, …) implements this contract
 * so Studio can call validate/render/diff/deploy uniformly.
 *
 * IR is the input IR type (typically IRPackage from delivery/ir-builder.ts).
 * Output is the rendered artifact type (TMDL strings, ZIP bytes, YAML, …).
 */

export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

export interface DiffEntry {
  path: string;
  kind: 'added' | 'removed' | 'changed';
  before?: string;
  after?: string;
}

export interface DeployResult {
  success: boolean;
  message: string;
  details?: Record<string, unknown>;
}

/**
 * Core adapter contract.  Implement all four methods for a fully-capable connector.
 */
export interface Adapter<IR, Output> {
  /** Human-readable adapter name (e.g. "fabric", "metabase"). */
  readonly name: string;

  /**
   * Validate the IR against adapter-specific constraints.
   * Returns errors and warnings without producing any output.
   */
  validate(ir: IR): ValidationResult | Promise<ValidationResult>;

  /**
   * Render IR → adapter-specific output.
   * Must not have side effects (no file writes, no network calls).
   */
  render(ir: IR): Output | Promise<Output>;

  /**
   * Compute a semantic diff between two IRs as rendered by this adapter.
   * Returns an array of human-readable change descriptions.
   */
  diff(before: IR, after: IR): DiffEntry[] | Promise<DiffEntry[]>;

  /**
   * Deploy a previously rendered output to the live target system.
   * Requires credentials appropriate for the target platform.
   */
  deploy(
    output: Output,
    targetUrl: string,
    credentials?: Record<string, string>,
  ): DeployResult | Promise<DeployResult>;
}

/** Base class with default diff and deploy implementations. */
export abstract class BaseAdapter<IR, Output> implements Adapter<IR, Output> {
  abstract readonly name: string;
  abstract validate(ir: IR): ValidationResult | Promise<ValidationResult>;
  abstract render(ir: IR): Output | Promise<Output>;

  diff(_before: IR, _after: IR): DiffEntry[] {
    return [];
  }

  deploy(_output: Output, _targetUrl: string, _credentials?: Record<string, string>): DeployResult {
    return { success: false, message: `${this.name}.deploy() is not yet implemented` };
  }
}

/** Type guard: checks that an object looks like an Adapter. */
export function isAdapter<IR, Output>(obj: unknown): obj is Adapter<IR, Output> {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    typeof (obj as Record<string, unknown>).name === 'string' &&
    typeof (obj as Record<string, unknown>).validate === 'function' &&
    typeof (obj as Record<string, unknown>).render === 'function' &&
    typeof (obj as Record<string, unknown>).diff === 'function' &&
    typeof (obj as Record<string, unknown>).deploy === 'function'
  );
}
