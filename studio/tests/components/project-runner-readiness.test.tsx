import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ProjectRunnerReadiness } from '@/components/project/project-runner-readiness';
import type { RunnerCheck } from '@/lib/bridge/project-runner';

afterEach(cleanup);
const checks: RunnerCheck[] = [
  { id: 'cli', title: 'Fabric CLI', state: 'missing', detail: 'Executable was not found.', action: 'Make the trusted fab installation available on the host PATH.' },
  { id: 'identity', title: 'Identity reference', state: 'configured', detail: 'Reference present.', action: 'Verify the identity separately.' },
  { id: 'tenant', title: 'Tenant acceptance', state: 'not_verified', detail: 'No live test was performed.', action: 'Follow the authorized acceptance procedure.' },
];
describe('readiness configuration and evidence separation', () => {
  it('shows blockers first and keeps resolved checks expandable', () => {
    const refresh = vi.fn();
    render(<ProjectRunnerReadiness checks={checks} loading={false} unavailable={false} refresh={refresh} busy={false} />);
    expect(screen.getByRole('status').textContent).toContain('1 configuration prerequisite needs');
    fireEvent.click(screen.getByText('Fabric CLI'));
    expect(screen.getByText(/Make the trusted fab installation/)).toBeTruthy();
    expect(screen.getByText('Configured prerequisites (1)').closest('details')?.open).toBe(false);
    expect(screen.getByText('Operational evidence still required (1)')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Recheck readiness' })); expect(refresh).toHaveBeenCalledOnce();
  });
  it('does not equate all configured checks with live readiness', () => {
    render(<ProjectRunnerReadiness checks={[checks[1]]} loading={false} unavailable={false} refresh={vi.fn()} busy={false} />);
    expect(screen.getByRole('status').textContent).toContain('Live acceptance is still required');
  });
  it('blocks duplicate refresh while checking and distinguishes unavailable from satisfied', () => {
    const view = render(<ProjectRunnerReadiness checks={[]} loading={true} unavailable={false} refresh={vi.fn()} busy={false} />);
    expect((screen.getByRole('button', { name: 'Checking…' }) as HTMLButtonElement).disabled).toBe(true);
    view.rerender(<ProjectRunnerReadiness checks={[]} loading={false} unavailable={true} refresh={vi.fn()} busy={false} />);
    expect(screen.getByRole('status').textContent).toContain('unavailable');
  });
});
