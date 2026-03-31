import { describe, it, expect } from 'vitest';
import { loadAllSpines, loadSpine, loadSpineMap } from '@/lib/core/spine-loader';

describe('spine-loader', () => {
  it('loadAllSpines returns an array of spines', async () => {
    const spines = await loadAllSpines();
    expect(Array.isArray(spines)).toBe(true);
    expect(spines.length).toBeGreaterThan(0);
  });

  it('each spine has required fields', async () => {
    const spines = await loadAllSpines();
    for (const s of spines) {
      expect(s.id).toBeTruthy();
      expect(s.name).toBeTruthy();
      expect(s.schema_version).toBe('1.0');
      expect(s.escalation_logic.escalation_path.length).toBe(3);
    }
  });

  it('escalation path has correct level order', async () => {
    const spines = await loadAllSpines();
    for (const s of spines) {
      const levels = s.escalation_logic.escalation_path.map((p) => p.level);
      expect(levels).toEqual([
        'EarlyWarning',
        'RequiredIntervention',
        'PrescriptiveExecution',
      ]);
    }
  });

  it('loadSpine returns a specific spine by ID', async () => {
    const spine = await loadSpine('DEC-SPINE-COM-CUSTOMER_VALUE');
    expect(spine).not.toBeNull();
    expect(spine?.name).toBe('Customer Value and Retention Discipline');
  });

  it('loadSpine returns null for unknown ID', async () => {
    const spine = await loadSpine('NONEXISTENT');
    expect(spine).toBeNull();
  });

  it('loadSpineMap returns a Map keyed by ID', async () => {
    const map = await loadSpineMap();
    expect(map instanceof Map).toBe(true);
    expect(map.size).toBeGreaterThan(0);
    for (const [key, val] of map) {
      expect(key).toBe(val.id);
    }
  });
});
