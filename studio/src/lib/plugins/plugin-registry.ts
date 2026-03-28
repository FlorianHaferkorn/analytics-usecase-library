/**
 * Plugin Registry — In-memory registry for managing plugins.
 *
 * Provides registration, lifecycle management, and hook-based event emission.
 */

import type { PluginManifest, RegisteredPlugin, PluginHook } from './plugin-types';

type HookHandler = (data: unknown) => void;

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
    return registered;
  }

  unregister(pluginId: string): boolean {
    const plugin = this.plugins.get(pluginId);
    if (!plugin) return false;

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

  onHook(hook: PluginHook, handler: HookHandler): () => void {
    if (!this.hookHandlers.has(hook)) {
      this.hookHandlers.set(hook, new Set());
    }
    this.hookHandlers.get(hook)!.add(handler);
    return () => this.hookHandlers.get(hook)?.delete(handler);
  }

  emit(hook: PluginHook, data: unknown): void {
    const handlers = this.hookHandlers.get(hook);
    if (!handlers) return;
    for (const handler of handlers) {
      try {
        handler(data);
      } catch {
        // Isolate plugin errors — don't let one plugin crash others
      }
    }
  }

  clear(): void {
    this.plugins.clear();
    this.hookHandlers.clear();
  }

  get size(): number {
    return this.plugins.size;
  }
}

/** Singleton plugin registry. */
export const pluginRegistry = new PluginRegistryImpl();
