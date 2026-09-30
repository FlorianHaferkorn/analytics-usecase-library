/**
 * Tests for Hook Contracts — typed payloads for plugin hooks.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { pluginRegistry } from '@/lib/plugins/plugin-registry';
import { ALL_HOOKS } from '@/lib/plugins/hook-contracts';
import type { HookPayloadMap } from '@/lib/plugins/hook-contracts';

describe('hook-contracts', () => {
  beforeEach(() => {
    pluginRegistry.clear();
  });

  it('ALL_HOOKS contains all five hook names', () => {
    expect(ALL_HOOKS).toContain('onBracketLoad');
    expect(ALL_HOOKS).toContain('onKpiEvaluate');
    expect(ALL_HOOKS).toContain('onThemeChange');
    expect(ALL_HOOKS).toContain('onExport');
    expect(ALL_HOOKS).toContain('onApproval');
    expect(ALL_HOOKS).toHaveLength(5);
  });

  it('emits onBracketLoad with typed payload', () => {
    const handler = vi.fn();
    pluginRegistry.onHook('onBracketLoad', handler);

    const payload: HookPayloadMap['onBracketLoad'] = {
      bracketId: 'UC001',
      kpiIds: ['KPI-COM-013'],
      status: 'draft',
    };
    pluginRegistry.emit('onBracketLoad', payload);
    expect(handler).toHaveBeenCalledWith(payload);
  });

  it('emits onKpiEvaluate with typed payload', () => {
    const handler = vi.fn();
    pluginRegistry.onHook('onKpiEvaluate', handler);

    const payload: HookPayloadMap['onKpiEvaluate'] = {
      kpiId: 'KPI-COM-013',
      value: 28.5,
      previousValue: 30.0,
      delta: -1.5,
    };
    pluginRegistry.emit('onKpiEvaluate', payload);
    expect(handler).toHaveBeenCalledWith(payload);
  });

  it('emits onExport with typed payload', () => {
    const handler = vi.fn();
    pluginRegistry.onHook('onExport', handler);

    const payload: HookPayloadMap['onExport'] = {
      format: 'fabric',
      bracketId: 'UC001',
      timestamp: '2026-01-01T00:00:00Z',
    };
    pluginRegistry.emit('onExport', payload);
    expect(handler).toHaveBeenCalledWith(payload);
  });

  it('emits onApproval with typed payload', () => {
    const handler = vi.fn();
    pluginRegistry.onHook('onApproval', handler);

    const payload: HookPayloadMap['onApproval'] = {
      bracketId: 'UC001',
      action: 'approve',
      actor: 'admin@co.com',
      status: 'approved',
    };
    pluginRegistry.emit('onApproval', payload);
    expect(handler).toHaveBeenCalledWith(payload);
  });

  it('emits onThemeChange with typed payload', () => {
    const handler = vi.fn();
    pluginRegistry.onHook('onThemeChange', handler);

    const payload: HookPayloadMap['onThemeChange'] = {
      primary: '#00D4AA',
      secondary: '#FFB800',
      background: '#1E293B',
      fontFamily: 'Inter',
    };
    pluginRegistry.emit('onThemeChange', payload);
    expect(handler).toHaveBeenCalledWith(payload);
  });
});
