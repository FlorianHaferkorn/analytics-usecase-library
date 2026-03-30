/**
 * Plugins API — List, register, and manage plugins.
 */

import { pluginRegistry } from '@/lib/plugins/plugin-registry';
import { loadPluginManifests } from '@/lib/plugins/plugin-loader';
import type { PluginManifest } from '@/lib/plugins/plugin-types';
import { requireAuth } from '@/lib/auth/session';

export async function GET() {
  // Auto-register discovered plugins that aren't already registered
  const manifests = loadPluginManifests();
  for (const manifest of manifests) {
    if (!pluginRegistry.get(manifest.id)) {
      try { pluginRegistry.register(manifest); } catch { /* already registered */ }
    }
  }

  const plugins = pluginRegistry.getAll();
  return Response.json({ plugins });
}

export async function POST(request: Request) {
  const [, authError] = await requireAuth();
  if (authError) return authError;

  const body = await request.json();
  const manifest = body as PluginManifest;

  if (!manifest.id || !manifest.name || !manifest.type) {
    return Response.json({ error: 'Invalid manifest' }, { status: 400 });
  }

  try {
    const registered = pluginRegistry.register(manifest);
    return Response.json({ plugin: registered }, { status: 201 });
  } catch (e) {
    return Response.json({ error: (e as Error).message }, { status: 409 });
  }
}

export async function PUT(request: Request) {
  const [, authError] = await requireAuth();
  if (authError) return authError;

  const body = await request.json();
  const { pluginId, enabled } = body as { pluginId: string; enabled: boolean };
  const ok = pluginRegistry.setEnabled(pluginId, enabled);
  if (!ok) return Response.json({ error: 'Plugin not found' }, { status: 404 });
  return Response.json({ ok: true });
}

export async function DELETE(request: Request) {
  const [, authError] = await requireAuth();
  if (authError) return authError;

  const { searchParams } = new URL(request.url);
  const pluginId = searchParams.get('pluginId');
  if (!pluginId) return Response.json({ error: 'pluginId required' }, { status: 400 });
  const ok = pluginRegistry.unregister(pluginId);
  if (!ok) return Response.json({ error: 'Plugin not found' }, { status: 404 });
  return Response.json({ ok: true });
}
