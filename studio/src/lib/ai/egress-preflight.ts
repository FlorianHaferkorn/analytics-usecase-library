import 'server-only';
import { createHash, randomUUID } from 'node:crypto';
import { evaluateAiDataHandling } from './data-handling-policy';
import { logAuditEvent, type AuditEvent } from '@/lib/db/audit-repo';

export const AI_EGRESS_PREFLIGHT_CONTRACT_VERSION = 'ai-egress-preflight/1.0.0';
const DEFAULT_MAX_PAYLOAD_BYTES = 1_048_576;

type Finding = { rule_id: string; category: string };
type JsonRecord = Record<string, unknown>;

const RULES: Array<[string, string, RegExp]> = [
  ['secret.private_key', 'secret', /-----BEGIN(?: [A-Z0-9]+)? PRIVATE KEY-----/gi],
  ['secret.bearer', 'secret', /\bBearer\s+[A-Za-z0-9._~+/=-]{16,}/gi],
  ['secret.jwt', 'secret', /\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b/g],
  ['secret.assignment', 'secret', /\b(?:api[_-]?key|client[_-]?secret|password|passwd|access[_-]?token|refresh[_-]?token)\s*[:=]\s*["']?[A-Za-z0-9_./+~=-]{8,}/gi],
  ['pii.email', 'pii', /(?<![\w.+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![\w.-])/gi],
  ['pii.phone', 'pii', /(?<!\w)(?:\+|00)\d{1,3}[\s()./-]*(?:\d[\s()./-]*){7,14}(?!\w)/g],
  ['identifier.uuid', 'identifier', /\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b/gi],
  ['path.user_home_windows', 'identifier', /\b[A-Z]:\\Users\\[^\\\s"']+/gi],
  ['path.user_home_posix', 'identifier', /(?<!\w)\/(?:home|Users)\/[^/\s"']+/g],
];
const IBAN = /\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]){11,30}\b/gi;

function stable(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(stable);
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.entries(value as JsonRecord)
      .filter(([, item]) => item !== undefined && typeof item !== 'function')
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, item]) => [key, stable(item)]));
  }
  return value;
}

export function canonicalPayload(payload: unknown): string {
  return JSON.stringify(stable(payload));
}

function escaped(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function validIban(candidate: string): boolean {
  const value = candidate.replace(/\s+/g, '').toUpperCase();
  if (value.length < 15 || value.length > 34 || !/^[A-Z]{2}\d{2}[A-Z0-9]+$/.test(value)) return false;
  const expanded = (value.slice(4) + value.slice(0, 4)).replace(/[A-Z]/g, (ch) => String(ch.charCodeAt(0) - 55));
  let remainder = 0;
  for (const digit of expanded) remainder = (remainder * 10 + Number(digit)) % 97;
  return remainder === 1;
}

function maskAllowlist(text: string, values: string[]): string {
  let masked = text;
  for (const value of [...new Set(values.filter(Boolean))].sort((a, b) => b.length - a.length)) {
    masked = masked.replace(new RegExp(escaped(value), 'gi'), '<ALLOWLISTED>');
  }
  return masked;
}

export function scanSensitiveData(payloadText: string, options: { blockedTerms?: string[]; allowlist?: string[] } = {}): Finding[] {
  const text = maskAllowlist(payloadText, options.allowlist ?? []);
  const findings: Finding[] = [];
  for (const [ruleId, category, pattern] of RULES) {
    pattern.lastIndex = 0;
    const inspected = category === 'secret' ? payloadText : text;
    findings.push(...Array.from(inspected.matchAll(pattern), () => ({ rule_id: ruleId, category })));
  }
  IBAN.lastIndex = 0;
  for (const match of text.matchAll(IBAN)) if (validIban(match[0])) findings.push({ rule_id: 'pii.iban', category: 'pii' });
  for (const term of [...new Set((options.blockedTerms ?? []).map((value) => value.trim()).filter(Boolean))].sort()) {
    findings.push(...Array.from(text.matchAll(new RegExp(escaped(term), 'gi')), () => ({ rule_id: 'customer.blocked_term', category: 'customer_term' })));
  }
  return findings;
}

export interface AiEgressEvidence extends JsonRecord {
  contract_version: string;
  event_id: string;
  occurred_at: string;
  decision: 'allow' | 'block';
  payload_sha256: string;
  payload_bytes: number;
  block_reasons: string[];
  rule_ids: string[];
}

export function buildAiEgressEvidence(input: {
  profile: JsonRecord;
  context: JsonRecord;
  payload: unknown;
  approvalGranted?: boolean;
  now?: () => Date;
}): AiEgressEvidence {
  const canonical = canonicalPayload(input.payload);
  const payloadBytes = Buffer.byteLength(canonical, 'utf8');
  const policy = (input.profile.data_handling ?? {}) as JsonRecord;
  const scanPolicy = (policy.scan_policy ?? {}) as JsonRecord;
  const findings = scanSensitiveData(canonical, {
    blockedTerms: (scanPolicy.blocked_terms as string[] | undefined) ?? [],
    allowlist: (scanPolicy.allowlist as string[] | undefined) ?? [],
  });
  const findingCounts: Record<string, number> = {};
  for (const finding of findings) findingCounts[finding.category] = (findingCounts[finding.category] ?? 0) + 1;
  const provider = String(input.profile.provider ?? 'unknown').toLowerCase();
  const boundary = String(policy.processing_boundary ?? 'external_cloud').toLowerCase();
  const blockReasons: string[] = [];
  let handlingContract: string | null = null;
  try { handlingContract = String(evaluateAiDataHandling(input.profile, input.context).decision ? 'ai-data-handling-policy/1.0.0' : ''); }
  catch { blockReasons.push('data_handling_policy'); }
  if (input.approvalGranted !== true) blockReasons.push('project_approval_missing');
  if (payloadBytes > Number(scanPolicy.max_payload_bytes ?? DEFAULT_MAX_PAYLOAD_BYTES)) blockReasons.push('payload_size');
  if (findingCounts.secret) blockReasons.push('secret_detected');
  if (boundary === 'external_cloud' && findings.length) blockReasons.push('sensitive_data_external_boundary');
  const reasons = [...new Set(blockReasons)].sort();
  const occurredAt = (input.now ?? (() => new Date()))().toISOString();
  const payloadSha = createHash('sha256').update(canonical).digest('hex');
  return Object.freeze({
    contract_version: AI_EGRESS_PREFLIGHT_CONTRACT_VERSION,
    event_id: `aie-${randomUUID()}`,
    occurred_at: occurredAt,
    decision: reasons.length ? 'block' : 'allow',
    payload_sha256: payloadSha,
    payload_bytes: payloadBytes,
    classification: String(input.context.classification ?? 'unknown').toLowerCase(),
    data_form: String(input.context.data_form ?? '').toLowerCase(),
    purpose: String(input.context.purpose ?? '').toLowerCase(),
    processing_boundary: boundary,
    provider,
    model: String(input.profile.model ?? ''),
    finding_count: findings.length,
    finding_counts: Object.fromEntries(Object.entries(findingCounts).sort()),
    rule_ids: [...new Set(findings.map((finding) => finding.rule_id))].sort(),
    block_reasons: reasons,
    data_handling_contract: handlingContract,
  });
}

export function persistAiEgressEvidence(evidence: AiEgressEvidence, projectId: string, actor: string): AuditEvent {
  const forbidden = ['payload', 'prompt', 'system', 'user', 'matches', 'redacted_text'];
  if (forbidden.some((key) => Object.hasOwn(evidence, key))) throw new Error('AI egress evidence contains a forbidden content field');
  return logAuditEvent(
    'ai_egress', evidence.event_id, evidence.decision === 'allow' ? 'allow' : 'block',
    { before: null, after: evidence }, projectId, actor,
  );
}
