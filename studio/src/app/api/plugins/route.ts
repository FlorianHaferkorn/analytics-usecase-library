/**
 * Plugins API — List, register, and manage plugins.
 */

import { pluginRegistry } from '@/lib/plugins/plugin-registry';
import { loadPluginManifests } from '@/lib/plugins/plugin-loader';
import type { PluginManifest } from '@/lib/plugins/plugin-types';
import { requireAuth } from '@/lib/auth/session';
import { auditWithKnownActor } from '@/lib/db/audit-helpers';
import { apiSuccess, apiCreated, apiError, apiValidationError } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';

export async function GET() {
  const manifests = loadPluginManifests();
  for (const manifest of manifests) {
    if (!pluginRegistry.get(manifest.id)) {
      try { pluginRegistry.register(manifest); } catch { /* already registered */ }
    }
  }

  const plugins = pluginRegistry.getAll();
  return apiSuccess({ plugins });
}

export async function POST(request: Request) {
  const [user, authError] = await requireAuth();
  if (authError) return authError;

  const body = await request.json();
  const manifest = body as PluginManifest;

  if (!manifest.id || !manifest.name || !manifest.type) {
    return apiValidationError(['Plugin manifest requires id, name, and type']);
  }

  try {
    const registered = pluginRegistry.register(manifest);
    auditWithKnownActor(user.email, 'plugin', manifest.id, 'create', {
      before: null,
      after: { name: manifest.name, type: manifest.type },
    });
    return apiCreated({ plugin: registered });
  } catch (e) {
    return apiError(ErrorCode.CONFLICT, (e as Error).message, 409);
  }
}

export async function PUT(request: Request) {
  const [user, authError] = await requireAuth();
  if (authError) return authError;

  const body = await request.json();
  const { pluginId, enabled } = body as { pluginId: string; enabled: boolean };
  const ok = pluginRegistry.setEnabled(pluginId, enabled);
  if (!ok) return apiError(ErrorCode.NOT_FOUND, 'Plugin not found', 404);

  auditWithKnownActor(user.email, 'plugin', pluginId, 'update', {
    before: null,
    after: { enabled },
  });

  return apiSuccess({ ok: true });
}

export async function DELETE(request: Request) {
  const [user, authError] = await requireAuth();
  if (authError) return authError;

  const { searchParams } = new URL(request.url);
  const pluginId = searchParams.get('pluginId');
  if (!pluginId) return apiValidationError(['pluginId required']);
  const ok = pluginRegistry.unregister(pluginId);
  if (!ok) return apiError(ErrorCode.NOT_FOUND, 'Plugin not found', 404);

  auditWithKnownActor(user.email, 'plugin', pluginId, 'delete', {
    before: { pluginId },
    after: null,
  });

  return apiSuccess({ ok: true });
}
