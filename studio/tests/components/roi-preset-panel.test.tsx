import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { RoiPresetPanel } from '@/components/roi/roi-preset-panel';

vi.mock('@/lib/store/project-store', () => ({
  useProjectStore: (selector: (state: { projectId: string }) => unknown) => selector({ projectId: 'demo' }),
}));

const fetchMock = vi.fn();
const props = { kpiId: 'KPI-COM-005', golden20Ids: ['KPI-COM-005'], onKpiChange: vi.fn() };
const preset = {
  kpi_id: props.kpiId, label: 'Net Sales',
  baseline_range: { min: 1000, likely: 2000, max: 3000, unit: 'units' },
  target_range: { min: 3000, likely: 4000, max: 5000, unit: 'units' },
  time_horizon_months: 12, driver_notes: [],
};

beforeEach(() => { fetchMock.mockReset(); vi.stubGlobal('fetch', fetchMock); });

describe('Value assumptions panel', () => {
  it('uses the explicit library route and never invents a currency or benchmark', async () => {
    fetchMock.mockResolvedValue(new Response(JSON.stringify({ preset }), { status: 200 }));
    render(<RoiPresetPanel {...props} />);
    expect(await screen.findByText('2000 units')).toBeTruthy();
    expect(fetchMock.mock.calls[0][0]).toBe('/api/core/presets/KPI-COM-005');
    expect(screen.queryByText(/Industry-benchmarked/)).toBeNull();
    expect(screen.queryByText('€2k')).toBeNull();
  });

  it('distinguishes an unavailable preset from a request error', async () => {
    fetchMock.mockResolvedValue(new Response(null, { status: 404 }));
    render(<RoiPresetPanel {...props} />);
    expect(await screen.findByText(/No illustrative ranges are available/)).toBeTruthy();
    expect(screen.queryByRole('alert')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Try again' })).toBeNull();
  });

  it('offers retry after a network failure and clears the error on success', async () => {
    fetchMock.mockRejectedValueOnce(new TypeError('Failed to fetch'))
      .mockResolvedValueOnce(new Response(JSON.stringify({ preset }), { status: 200 }));
    render(<RoiPresetPanel {...props} />);
    expect((await screen.findByRole('alert')).textContent).toContain('Check your connection');
    fireEvent.click(screen.getByRole('button', { name: 'Try again' }));
    expect(await screen.findByText('2000 units')).toBeTruthy();
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('does not retain the previous KPI when selection is cleared', async () => {
    fetchMock.mockResolvedValue(new Response(JSON.stringify({ preset }), { status: 200 }));
    const view = render(<RoiPresetPanel {...props} />);
    expect(await screen.findByText('2000 units')).toBeTruthy();
    view.rerender(<RoiPresetPanel {...props} kpiId={null} />);
    expect(screen.queryByText('2000 units')).toBeNull();
    expect(screen.getByText('Select a KPI to review its available assumptions.')).toBeTruthy();
  });
});
