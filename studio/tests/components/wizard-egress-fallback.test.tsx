import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { Wizard } from '@/components/ui/wizard';

vi.mock('@/components/ai/ai-field', () => ({
  AiField: ({ value, onChange, fieldLabel, multiline }: {
    value: string; onChange: (value: string) => void; fieldLabel: string; multiline?: boolean;
  }) => multiline
    ? <textarea aria-label={fieldLabel} value={value} onChange={(event) => onChange(event.target.value)} />
    : <input aria-label={fieldLabel} value={value} onChange={(event) => onChange(event.target.value)} />,
}));

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

describe('Wizard while AI egress is not approved', () => {
  it('keeps a clearly labeled manual review and save path', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ name: 'Sales margin', description: 'Review sales margin by customer.' }) })
      .mockResolvedValueOnce({ ok: false, status: 403, json: async () => ({ code: 'AI_EGRESS_NOT_APPROVED', error: 'AI processing paused.' }) });
    vi.stubGlobal('fetch', fetchMock);
    const onSave = vi.fn();
    render(<Wizard open onClose={vi.fn()} onSave={onSave} />);
    fireEvent.click(screen.getByRole('button', { name: /Continue/ }));
    fireEvent.change(screen.getByLabelText('Use Case Description'), { target: { value: 'Review sales margin by customer.' } });
    fireEvent.click(screen.getByRole('button', { name: /Generate draft/ }));

    await waitFor(() => expect(screen.getByRole('status').textContent).toContain('Manual draft'));
    const save = screen.getByRole('button', { name: /Save to framework/ });
    expect((save as HTMLButtonElement).disabled).toBe(true);
    fireEvent.change(screen.getByLabelText('Reference'), { target: { value: 'sales_margin' } });
    fireEvent.change(screen.getByLabelText('Domain'), { target: { value: 'Commercial' } });
    fireEvent.change(screen.getByLabelText('Type'), { target: { value: 'ratio' } });
    fireEvent.change(screen.getByLabelText('Grain'), { target: { value: 'monthly by customer' } });
    expect((save as HTMLButtonElement).disabled).toBe(false);
    fireEvent.click(save);
    expect(onSave).toHaveBeenCalledWith('kpi', expect.objectContaining({
      name: 'Sales margin', ref: 'sales_margin', domain: 'Commercial', type: 'ratio', grain: 'monthly by customer',
    }));
    expect(fetchMock).toHaveBeenCalledTimes(2);
  }, 15_000);
});
