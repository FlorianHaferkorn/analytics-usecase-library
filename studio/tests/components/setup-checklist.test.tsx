import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SetupChecklist } from '@/components/setup/setup-checklist';
import type { SetupReadiness } from '@/lib/setup/preflight';

const ready: SetupReadiness = {
  ready: true,
  blockers: [],
  checks: [
    { key: 'llm_key', label: 'LLM-Key (BYO)', status: 'ok', detail: 'anthropic-Key erkannt', required: true },
    { key: 'python_bridge', label: 'Python-Bridge', status: 'ok', detail: 'erreichbar', required: true },
    { key: 'auth', label: 'Auth', status: 'warn', detail: 'nur Dev-Credentials', required: false },
  ],
};

describe('SetupChecklist', () => {
  it('shows a ready verdict and renders each check with its status', () => {
    render(<SetupChecklist readiness={ready} />);
    expect(screen.getByTestId('setup-verdict').getAttribute('data-ready')).toBe('true');
    expect(screen.getByTestId('setup-check-llm_key').getAttribute('data-status')).toBe('ok');
    expect(screen.getByTestId('setup-check-auth').getAttribute('data-status')).toBe('warn');
    expect(screen.getByText(/optional/)).toBeDefined();
  });

  it('shows a blocked verdict that names the blockers', () => {
    const blocked: SetupReadiness = {
      ready: false,
      blockers: ['LLM-Key (BYO)'],
      checks: [{ key: 'llm_key', label: 'LLM-Key (BYO)', status: 'missing', detail: 'kein Key', required: true }],
    };
    render(<SetupChecklist readiness={blocked} />);
    const verdict = screen.getByTestId('setup-verdict');
    expect(verdict.getAttribute('data-ready')).toBe('false');
    expect(verdict.textContent).toMatch(/LLM-Key/);
    expect(screen.getByTestId('setup-check-llm_key').getAttribute('data-status')).toBe('missing');
  });
});
