import { describe, it, expect, beforeEach, vi } from 'vitest';
import { pluginRegistry } from '@/lib/plugins/plugin-registry';
import type { PluginManifest } from '@/lib/plugins/plugin-types';

function makeManifest(overrides: Partial<PluginManifest> = {}): PluginManifest {
  return {
    id: 'test-plugin',
    name: 'Test Plugin',
    version: '1.0.0',
    author: 'Test Author',
    type: 'tool',
    description: 'A test plugin',
    entrypoint: 'index.ts',
    hooks: [],
    ...overrides,
  };
}

describe('PluginRegistry', () => {
  beforeEach(() => {
    pluginRegistry.clear();
  });

  it('registers a plugin and retrieves it', () => {
    const manifest = makeManifest();
    const registered = pluginRegistry.register(manifest);

    expect(registered.manifest.id).toBe('test-plugin');
    expect(registered.enabled).toBe(true);
    expect(registered.registeredAt).toBeGreaterThan(0);
    expect(pluginRegistry.get('test-plugin')).toBe(registered);
  });

  it('prevents duplicate registration', () => {
    pluginRegistry.register(makeManifest());
    expect(() => pluginRegistry.register(makeManifest())).toThrow(
      'Plugin "test-plugin" is already registered',
    );
  });

  it('unregisters a plugin', () => {
    pluginRegistry.register(makeManifest());
    expect(pluginRegistry.unregister('test-plugin')).toBe(true);
    expect(pluginRegistry.get('test-plugin')).toBeUndefined();
    expect(pluginRegistry.size).toBe(0);
  });

  it('returns false when unregistering unknown plugin', () => {
    expect(pluginRegistry.unregister('nonexistent')).toBe(false);
  });

  it('lists all registered plugins', () => {
    pluginRegistry.register(makeManifest({ id: 'plugin-a', name: 'Plugin A' }));
    pluginRegistry.register(makeManifest({ id: 'plugin-b', name: 'Plugin B' }));

    const all = pluginRegistry.getAll();
    expect(all).toHaveLength(2);
    expect(all.map((p) => p.manifest.id).sort()).toEqual(['plugin-a', 'plugin-b']);
  });

  it('enables and disables plugins', () => {
    pluginRegistry.register(makeManifest());

    expect(pluginRegistry.setEnabled('test-plugin', false)).toBe(true);
    expect(pluginRegistry.get('test-plugin')!.enabled).toBe(false);

    expect(pluginRegistry.setEnabled('test-plugin', true)).toBe(true);
    expect(pluginRegistry.get('test-plugin')!.enabled).toBe(true);

    expect(pluginRegistry.setEnabled('nonexistent', true)).toBe(false);
  });

  it('emits hook events to registered handlers', () => {
    const handler = vi.fn();
    const unsubscribe = pluginRegistry.onHook('onKpiEvaluate', handler);

    pluginRegistry.emit('onKpiEvaluate', { kpiId: 'test', value: 42 });
    expect(handler).toHaveBeenCalledWith({ kpiId: 'test', value: 42 });

    unsubscribe();
    pluginRegistry.emit('onKpiEvaluate', { kpiId: 'test', value: 99 });
    expect(handler).toHaveBeenCalledTimes(1);
  });

  it('clears all plugins and hooks', () => {
    pluginRegistry.register(makeManifest());
    const handler = vi.fn();
    pluginRegistry.onHook('onBracketLoad', handler);

    pluginRegistry.clear();
    expect(pluginRegistry.size).toBe(0);
    expect(pluginRegistry.getAll()).toHaveLength(0);

    pluginRegistry.emit('onBracketLoad', { bracketId: 'UC001', kpiIds: [], status: 'draft' });
    expect(handler).not.toHaveBeenCalled();
  });
});
