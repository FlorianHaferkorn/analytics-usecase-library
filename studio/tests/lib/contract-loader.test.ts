import { describe, it, expect } from 'vitest';
import { loadAllContracts, loadContract, loadContractMap } from '@/lib/core/contract-loader';

describe('contract-loader', () => {
  it('loadAllContracts returns an array of contracts', async () => {
    const contracts = await loadAllContracts();
    expect(Array.isArray(contracts)).toBe(true);
    expect(contracts.length).toBeGreaterThan(0);
  });

  it('each contract has required fields', async () => {
    const contracts = await loadAllContracts();
    for (const c of contracts) {
      expect(c.domain).toBeTruthy();
      expect(c.version).toBeTruthy();
      expect(c.owner).toBeTruthy();
    }
  });

  it('contracts have dimension and fact arrays', async () => {
    const contracts = await loadAllContracts();
    for (const c of contracts) {
      expect(Array.isArray(c.dimension)).toBe(true);
      expect(Array.isArray(c.fact)).toBe(true);
    }
  });

  it('loadContract returns a specific contract by domain', async () => {
    const contracts = await loadAllContracts();
    if (contracts.length > 0) {
      const first = contracts[0];
      const found = await loadContract(first.domain);
      expect(found).not.toBeNull();
      expect(found?.domain).toBe(first.domain);
    }
  });

  it('loadContract returns null for unknown domain', async () => {
    const result = await loadContract('NONEXISTENT_DOMAIN');
    expect(result).toBeNull();
  });

  it('loadContractMap returns a Map keyed by domain', async () => {
    const map = await loadContractMap();
    expect(map instanceof Map).toBe(true);
    for (const [key, val] of map) {
      expect(key).toBe(val.domain);
    }
  });
});
