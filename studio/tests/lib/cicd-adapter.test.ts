import { describe, it, expect } from 'vitest';
import { generateGitHubWorkflow, generateValidationPipeline, generateDeployScript } from '@/lib/delivery/cicd-adapter';
import type { IRPackage } from '@/lib/delivery/ir-builder';

const mockIR: IRPackage = {
  useCaseId: 'UC001',
  title: 'Revenue Growth',
  domain: 'Finance',
  measures: [
    {
      id: 'KPI_001', name: 'Revenue', expression: 'SUM(Sales[Amount])',
      formatString: '#,0', calcType: 'sum', description: 'Total revenue',
      dependsOn: [], folder: 'Finance',
    },
  ],
  pages: [],
  actionCodes: ['AC_001'],
  warnings: [],
  metadata: { generatedAt: '2026-01-01T00:00:00Z', schemaVersion: '2.0' },
};

describe('generateGitHubWorkflow', () => {
  it('generates valid YAML structure', () => {
    const output = generateGitHubWorkflow([mockIR]);
    expect(output.filename).toBe('.github/workflows/deploy-fabric.yml');
    expect(output.content).toContain('name: Deploy to Fabric');
    expect(output.content).toContain('on:');
    expect(output.content).toContain('jobs:');
  });

  it('uses correct GitHub Actions secrets syntax', () => {
    const output = generateGitHubWorkflow([mockIR]);
    // Secrets should use ${{ secrets.X }} without backslash escape
    expect(output.content).toContain('${{ secrets.FABRIC_WORKSPACE_ID }}');
    expect(output.content).toContain('${{ secrets.FABRIC_TENANT_ID }}');
    // Should NOT have backslash-escaped references
    expect(output.content).not.toContain('\\${{ secrets');
  });

  it('uses correct needs.deploy.result expression', () => {
    const output = generateGitHubWorkflow([mockIR]);
    expect(output.content).toContain('${{ needs.deploy.result }}');
    expect(output.content).not.toContain('\\${{ needs');
  });

  it('interpolates use case IDs', () => {
    const output = generateGitHubWorkflow([mockIR]);
    expect(output.content).toContain('UC001');
  });
});

describe('generateDeployScript', () => {
  it('generates a Python deploy script', () => {
    const output = generateDeployScript([mockIR]);
    expect(output.filename).toBe('products/fabric/deploy.py');
    expect(output.content).toContain('def deploy_tmdl');
  });

  it('deploy_tmdl has actual API implementation', () => {
    const output = generateDeployScript([mockIR]);
    // Should NOT be a TODO stub
    expect(output.content).not.toContain('# TODO');
    // Should reference Fabric REST API
    expect(output.content).toContain('api.fabric.microsoft.com');
    expect(output.content).toContain('semanticmodels');
  });
});

describe('generateValidationPipeline', () => {
  it('generates a validation workflow', () => {
    const output = generateValidationPipeline([mockIR]);
    expect(output.filename).toBe('.github/workflows/validate-artifacts.yml');
    expect(output.content).toContain('name: Validate Analytics Artifacts');
    expect(output.content).toContain('npm run build');
  });
});
