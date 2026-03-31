/**
 * Tests for Plugin SDK — lifecycle, version checks, loader warnings.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { pluginRegistry } from '@/lib/plugins/plugin-registry';
import type { PluginManifest } from '@/lib/plugins/plugin-types';
import { checkVersionConflicts } from '@/lib/plugins/version-check';
import {
  createPluginContext,
  clearLifecycles,
} from '@/lib/plugins/lifecycle';

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

describe('plugin-lifecycle', () => {
  beforeEach(() => {
    pluginRegistry.clear();
    clearLifecycles();
  });

  it('calls onLoad when registering a plugin with lifecycle', () => {
    const onLoad = vi.fn();
    const manifest = makeManifest({
      lifecycle: { onLoad },
    });
    pluginRegistry.register(manifest);

    expect(onLoad).toHaveBeenCalledTimes(1);
    expect(onLoad).toHaveBeenCalledWith(
      expect.objectContaining({
        pluginId: 'test-plugin',
        pluginVersion: '1.0.0',
        studioVersion: '0.1.0',
      }),
    );
  });

  it('calls onUnload when unregistering a plugin with lifecycle', () => {
    const onUnload = vi.fn();
    const manifest = makeManifest({
      lifecycle: { onUnload },
    });
    pluginRegistry.register(manifest);
    pluginRegistry.unregister('test-plugin');

    expect(onUnload).toHaveBeenCalledTimes(1);
  });

  it('does not crash if lifecycle onLoad throws', () => {
    const manifest = makeManifest({
      lifecycle: {
        onLoad: () => { throw new Error('boom'); },
      },
    });
    expect(() => pluginRegistry.register(manifest)).not.toThrow();
    expect(pluginRegistry.get('test-plugin')).toBeDefined();
  });

  it('creates plugin context with correct fields', () => {
    const ctx = createPluginContext('my-plugin', '2.0.0');
    expect(ctx.pluginId).toBe('my-plugin');
    expect(ctx.pluginVersion).toBe('2.0.0');
    expect(ctx.studioVersion).toBe('0.1.0');
  });
});

describe('version-check', () => {
  it('returns empty array when no conflicts', () => {
    const manifests = [
      makeManifest({ id: 'a', version: '1.0.0' }),
      makeManifest({ id: 'b', version: '2.0.0' }),
    ];
    expect(checkVersionConflicts(manifests)).toHaveLength(0);
  });

  it('detects duplicate IDs with different versions', () => {
    const manifests = [
      makeManifest({ id: 'my-plugin', version: '1.0.0' }),
      makeManifest({ id: 'my-plugin', version: '2.0.0' }),
      makeManifest({ id: 'other', version: '1.0.0' }),
    ];
    const conflicts = checkVersionConflicts(manifests);
    expect(conflicts).toHaveLength(1);
    expect(conflicts[0].pluginId).toBe('my-plugin');
    expect(conflicts[0].versions).toEqual(['1.0.0', '2.0.0']);
  });

  it('ignores duplicate IDs with same version', () => {
    const manifests = [
      makeManifest({ id: 'a', version: '1.0.0' }),
      makeManifest({ id: 'a', version: '1.0.0' }),
    ];
    expect(checkVersionConflicts(manifests)).toHaveLength(0);
  });

  it('handles empty manifest array', () => {
    expect(checkVersionConflicts([])).toHaveLength(0);
  });
});
