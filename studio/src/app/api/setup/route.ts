/**
 * GET /api/setup — standalone / local-first readiness (I-6.5).
 *
 * Runs the live preflight checks a fresh installer needs (BYO LLM key, secrets
 * provider, Python bridge reachable, Core artifacts present, auth) and returns
 * an honest readiness verdict that names any blocker.
 */

import {
  authCheck,
  computeSetupReadiness,
  llmKeyCheck,
  secretsProviderCheck,
  type SetupCheck,
} from '@/lib/setup/preflight';
import { pingBridge } from '@/lib/bridge/superversion-bridge';
import { loadAllBrackets } from '@/lib/core/bracket-loader';
import { apiSuccess } from '@/lib/api/response';

export async function GET(): Promise<Response> {
  const ping = await pingBridge();
  const pythonBridge: SetupCheck = {
    key: 'python_bridge',
    label: 'Python-Bridge',
    status: ping.available ? 'ok' : 'missing',
    detail: ping.available
      ? `erreichbar (${ping.targetsAvailable.join(', ')})`
      : ping.error || 'nicht erreichbar',
    required: true,
  };

  let brackets = 0;
  try {
    brackets = (await loadAllBrackets()).length;
  } catch {
    brackets = 0;
  }
  const coreArtifacts: SetupCheck = {
    key: 'core_artifacts',
    label: 'Core-Artefakte',
    status: brackets > 0 ? 'ok' : 'missing',
    detail: brackets > 0 ? `${brackets} Use-Case-Bracket(s) gefunden` : 'keine Brackets unter core/usecases/',
    required: true,
  };

  const checks: SetupCheck[] = [
    llmKeyCheck(process.env),
    secretsProviderCheck(process.env),
    pythonBridge,
    coreArtifacts,
    authCheck(process.env),
  ];
  return apiSuccess(computeSetupReadiness(checks));
}
