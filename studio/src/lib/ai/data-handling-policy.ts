import 'server-only';
import { isIP } from 'node:net';

/** Neutral ai-data-handling-policy/1.0.0 semantics; not a project approval. */
const CLASSIFICATIONS = new Set(['public', 'internal_generic', 'customer_confidential', 'restricted', 'secret', 'unknown']);
const DATA_FORMS = new Set(['metadata', 'aggregates', 'schema', 'code', 'document_excerpt', 'raw_rows', 'synthetic']);
const PURPOSES = new Set(['studio_authoring', 'enduser_question', 'analytics_reasoning', 'analytics_advisory']);
const BOUNDARIES = new Set(['local', 'customer_managed_cloud', 'external_cloud']);
const NEVER_MODEL = new Set(['unknown', 'restricted', 'secret']);
const INTERNAL_SUFFIXES = ['.local', '.lan', '.internal', '.intranet', '.home.arpa', '.corp'];

type RecordValue = Record<string, unknown>;
export class AiDataHandlingViolation extends Error {}

function record(value: unknown): RecordValue | null {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as RecordValue : null;
}

function label(value: unknown): string {
  return typeof value === 'string' ? value.trim().toLowerCase() : '';
}

function stringSet(value: unknown, allowed: Set<string>): Set<string> | null {
  if (!Array.isArray(value) || !value.length || value.some((entry) => !allowed.has(entry))) return null;
  return new Set(value as string[]);
}

/** Conservative endpoint check; a provider name alone cannot establish locality. */
export function isInternalAiEndpoint(value: unknown): boolean {
  if (typeof value !== 'string') return false;
  try {
    const url = new URL(value);
    if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) return false;
    const host = url.hostname.replace(/^\[|\]$/g, '').replace(/\.$/, '').toLowerCase();
    if (!host) return false;
    if (isIP(host) === 4) {
      const parts = host.split('.').map(Number);
      return parts[0] === 10 || parts[0] === 127 ||
        (parts[0] === 172 && parts[1] >= 16 && parts[1] <= 31) ||
        (parts[0] === 192 && parts[1] === 168);
    }
    if (isIP(host) === 6) return host === '::1' || /^f[cd][0-9a-f]/.test(host);
    return host === 'localhost' || !host.includes('.') || INTERNAL_SUFFIXES.some((suffix) => host.endsWith(suffix));
  } catch {
    return false;
  }
}

export interface AiDataHandlingDecision {
  decision: 'allow';
  classification: string;
  data_form: string;
  purpose: string;
  processing_boundary: string;
  provider: string;
}

/**
 * Deterministic predicate for a *validated* model input. A positive result is
 * necessary but insufficient: the project approval, exact-payload scanner,
 * provider/region evidence and output checks are separate blocking gates.
 * Studio's live egress gate therefore remains default-deny.
 */
export function evaluateAiDataHandling(profileInput: unknown, contextInput: unknown): AiDataHandlingDecision {
  const profile = record(profileInput);
  const context = record(contextInput);
  const policy = record(profile?.data_handling);
  const provider = label(profile?.provider);
  const classification = label(context?.classification);
  const dataForm = label(context?.data_form);
  const purpose = label(context?.purpose);
  const boundary = label(policy?.processing_boundary);
  if (!profile || !context || !policy || !provider) throw new AiDataHandlingViolation('An explicit profile and data-handling policy are required.');
  if (!CLASSIFICATIONS.has(classification) || !DATA_FORMS.has(dataForm) || !PURPOSES.has(purpose) || !BOUNDARIES.has(boundary) || typeof context.redacted !== 'boolean') {
    throw new AiDataHandlingViolation('Unknown or missing classification, data form, purpose, boundary or redaction state.');
  }
  if (NEVER_MODEL.has(classification)) throw new AiDataHandlingViolation('This classification must never reach a model.');
  if (boundary === 'local' && !['local', 'mock'].includes(provider)) throw new AiDataHandlingViolation('External provider cannot claim a local boundary.');
  if (boundary === 'local' && provider === 'local' && profile.base_url !== undefined && !isInternalAiEndpoint(profile.base_url)) {
    throw new AiDataHandlingViolation('Local provider endpoint is not internal.');
  }
  const allowedClasses = stringSet(policy.allowed_classifications, CLASSIFICATIONS);
  const allowedForms = stringSet(policy.allowed_data_forms, DATA_FORMS);
  const allowedPurposes = stringSet(policy.allowed_purposes, PURPOSES);
  if (!allowedClasses || !allowedForms || !allowedPurposes || !allowedClasses.has(classification) || !allowedForms.has(dataForm) || !allowedPurposes.has(purpose)) {
    throw new AiDataHandlingViolation('Data class, form or purpose is not allowed by the profile.');
  }
  if (policy.provider_training_allowed !== false || !Number.isInteger(policy.prompt_retention_days) || (policy.prompt_retention_days as number) < 0 || typeof policy.require_redaction_for_egress !== 'boolean') {
    throw new AiDataHandlingViolation('Training, retention and egress-redaction terms must be explicit.');
  }
  if (classification === 'customer_confidential' && boundary === 'external_cloud') throw new AiDataHandlingViolation('Customer content cannot use external cloud.');
  if (boundary === 'customer_managed_cloud' && (typeof policy.boundary_evidence_ref !== 'string' || !policy.boundary_evidence_ref.trim())) {
    throw new AiDataHandlingViolation('Customer-managed boundary requires evidence.');
  }
  if (boundary === 'external_cloud' && classification !== 'public' && context.redacted !== true) {
    throw new AiDataHandlingViolation('Non-public external-cloud input must be redacted.');
  }
  return Object.freeze({ decision: 'allow', classification, data_form: dataForm, purpose, processing_boundary: boundary, provider });
}
