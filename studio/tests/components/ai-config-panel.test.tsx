import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AiConfigPanel } from '@/components/ai/ai-config-panel';
import { allowedActions, VALID_TRANSITIONS } from '@/lib/ai/config/governance-types';

describe('allowedActions (shared lifecycle rules)', () => {
  it('mirrors VALID_TRANSITIONS', () => {
    expect(allowedActions('draft')).toEqual(['submit']);
    expect(allowedActions('review')).toEqual(['approve', 'reject']);
    expect(allowedActions('approved')).toEqual(['reopen']);
    expect(allowedActions('rejected')).toEqual(['reopen']);
    // exhaustive parity with the table
    for (const s of Object.keys(VALID_TRANSITIONS) as (keyof typeof VALID_TRANSITIONS)[]) {
      expect(allowedActions(s)).toEqual(VALID_TRANSITIONS[s]);
    }
  });
});

describe('AiConfigPanel', () => {
  it('draft: shows save + submit, not approve', () => {
    render(<AiConfigPanel initialStatus="draft" initialConfig='{"schema_version":"1.0.0","layer":"L1"}' />);
    expect(screen.getByTestId('config-status').getAttribute('data-status')).toBe('draft');
    expect(screen.getByTestId('act-save')).toBeDefined();
    expect(screen.getByTestId('act-submit')).toBeDefined();
    expect(screen.queryByTestId('act-approve')).toBeNull();
  });

  it('review: shows approve + reject', () => {
    render(<AiConfigPanel initialStatus="review" />);
    expect(screen.getByTestId('act-approve')).toBeDefined();
    expect(screen.getByTestId('act-reject')).toBeDefined();
    expect(screen.queryByTestId('act-submit')).toBeNull();
  });

  it('none: only save (no transitions yet)', () => {
    render(<AiConfigPanel initialStatus="none" />);
    expect(screen.getByTestId('act-save')).toBeDefined();
    expect(screen.queryByTestId('act-submit')).toBeNull();
    expect(screen.queryByTestId('act-approve')).toBeNull();
  });

  it('approved: offers reopen', () => {
    render(<AiConfigPanel initialStatus="approved" />);
    expect(screen.getByTestId('act-reopen')).toBeDefined();
  });
});
