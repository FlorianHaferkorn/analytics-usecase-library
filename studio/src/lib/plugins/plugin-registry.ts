/**
 * Plugin Registry — In-memory registry for managing plugins.
 *
 * Provides registration, lifecycle management, and typed hook-based event emission.
 */

import type { PluginManifest, RegisteredPlugin, PluginHook } from './plugin-types';
import type { HookPayloadMap } from './hook-contracts';
import {
  registerLifecycle,
  removeLifecycle,
  getLifecycle,
  createPluginContext,
  clearLifecycles,
} from './lifecycle';

type HookHandler<H extends PluginHook = PluginHook> = (data: HookPayloadMap[H]) => void;

class PluginRegistryImpl {
  private plugins = new Map<string, RegisteredPlugin>();
  private hookHandlers = new Map<PluginHook, Set<HookHandler>>();

  register(manifest: PluginManifest): RegisteredPlugin {
    if (this.plugins.has(manifest.id)) {
      throw new Error(`Plugin "${manifest.id}" is already registered`);
    }

    const registered: RegisteredPlugin = {
      manifest,
      enabled: true,
      registeredAt: Date.now(),
    };

    this.plugins.set(manifest.id, registered);

    // Store and invoke lifecycle onLoad
    if (manifest.lifecycle) {
      registerLifecycle(manifest.id, manifest.lifecycle);
      const ctx = createPluginContext(manifest.id, manifest.version);
      try {
        manifest.lifecycle.onLoad?.(ctx);
      } catch {
        // Isolate lifecycle errors
      }
    }

    return registered;
  }

  unregister(pluginId: string): boolean {
    const plugin = this.plugins.get(pluginId);
    if (!plugin) return false;

    // Invoke lifecycle onUnload
    const lifecycle = getLifecycle(pluginId);
    if (lifecycle?.onUnload) {
      try {
        lifecycle.onUnload();
      } catch {
        // Isolate lifecycle errors
      }
    }
    removeLifecycle(pluginId);

    // Remove hook handlers for this plugin
    for (const handlers of this.hookHandlers.values()) {
      for (const handler of handlers) {
        handlers.delete(handler);
      }
    }

    return this.plugins.delete(pluginId);
  }

  get(pluginId: string): RegisteredPlugin | undefined {
    return this.plugins.get(pluginId);
  }

  getAll(): RegisteredPlugin[] {
    return Array.from(this.plugins.values());
  }

  setEnabled(pluginId: string, enabled: boolean): boolean {
    const plugin = this.plugins.get(pluginId);
    if (!plugin) return false;
    plugin.enabled = enabled;
    return true;
  }

  onHook<H extends PluginHook>(hook: H, handler: HookHandler<H>): () => void {
    if (!this.hookHandlers.has(hook)) {
      this.hookHandlers.set(hook, new Set());
    }
    this.hookHandlers.get(hook)!.add(handler as HookHandler);
    return () => this.hookHandlers.get(hook)?.delete(handler as HookHandler);
  }

  emit<H extends PluginHook>(hook: H, data: HookPayloadMap[H]): void {
    const handlers = this.hookHandlers.get(hook);
    if (!handlers) return;
    for (const handler of handlers) {
      try {
        (handler as HookHandler<H>)(data);
      } catch {
        // Isolate plugin errors — don't let one plugin crash others
      }
    }
  }

  clear(): void {
    this.plugins.clear();
    this.hookHandlers.clear();
    clearLifecycles();
  }

  get size(): number {
    return this.plugins.size;
  }
}

/** Singleton plugin registry. */
export const pluginRegistry = new PluginRegistryImpl();
