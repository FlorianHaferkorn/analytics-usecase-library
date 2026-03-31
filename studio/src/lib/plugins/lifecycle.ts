/**
 * Plugin Lifecycle — onLoad / onUnload callbacks.
 *
 * Plugins can optionally export lifecycle hooks that run when
 * they are registered or unregistered from the registry.
 */

export interface PluginContext {
  pluginId: string;
  pluginVersion: string;
  studioVersion: string;
}

export interface PluginLifecycle {
  onLoad?: (context: PluginContext) => void | Promise<void>;
  onUnload?: () => void | Promise<void>;
}

const STUDIO_VERSION = '0.1.0';

/** Create a PluginContext for a given plugin. */
export function createPluginContext(pluginId: string, pluginVersion: string): PluginContext {
  return {
    pluginId,
    pluginVersion,
    studioVersion: STUDIO_VERSION,
  };
}

const lifecycles = new Map<string, PluginLifecycle>();

/** Store lifecycle callbacks for a plugin. */
export function registerLifecycle(pluginId: string, lifecycle: PluginLifecycle): void {
  lifecycles.set(pluginId, lifecycle);
}

/** Get stored lifecycle for a plugin. */
export function getLifecycle(pluginId: string): PluginLifecycle | undefined {
  return lifecycles.get(pluginId);
}

/** Remove lifecycle callbacks (called on unregister). */
export function removeLifecycle(pluginId: string): boolean {
  return lifecycles.delete(pluginId);
}

/** Clear all lifecycle registrations. */
export function clearLifecycles(): void {
  lifecycles.clear();
}
