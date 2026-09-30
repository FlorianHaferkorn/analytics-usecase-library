import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { KpiSlider } from '@/components/simulator/kpi-slider';
import { driverSliderRange, normalizeSliderRange } from '@/lib/simulation/slider-range';
import { formatKpiValue, isTimeOrCountFormat, unitFromFormat } from '@/lib/format/kpi-value';

describe('Valid driver slider ranges', () => {
  it.each([
    [-4.7, '%', false],
    [-400, 'EUR', false],
    [0, 'EUR', false],
    [0, '%', false],
    [0, 'd', true],
    [150, '%', false],
  ])('contains baseline %s with a positive usable span', (base, unit, timeOrCount) => {
    const { minRange, maxRange } = driverSliderRange(base as number, unit as string, timeOrCount as boolean);
    expect(minRange).toBeLessThan(maxRange);
    expect(minRange).toBeLessThanOrEqual(base as number);
    expect(maxRange).toBeGreaterThanOrEqual(base as number);
    expect(maxRange - minRange).toBeGreaterThan(0);
  });

  it('normalizes reversed or equal legacy endpoints', () => {
    expect(normalizeSliderRange(-4.7, 0, -6.1)).toEqual({ min: -6.1, max: 0 });
    expect(normalizeSliderRange(0, 0, 0)).toEqual({ min: -1, max: 1 });
  });

  it('exposes an operable negative baseline and English accessible labels', () => {
    const onChange = vi.fn();
    render(<KpiSlider kpiId="KPI-COM-003" label="Plan variance" baseValue={-4.7} value={-4.7} unit="%" {...driverSliderRange(-4.7, '%', false)} onChange={onChange} />);
    const input = screen.getByRole('slider', { name: 'Plan variance' }) as HTMLInputElement;
    expect(Number(input.min)).toBe(-19.7);
    expect(Number(input.max)).toBe(10.3);
    expect(Number(input.step)).toBeGreaterThan(0);
    expect(input.getAttribute('aria-valuetext')).toBe('-4,7%; baseline -4,7%');
    fireEvent.change(input, { target: { value: '-3.5' } });
    expect(onChange).toHaveBeenCalledWith(-3.5);
  });

  it('groups large amounts and adds currency only when supplied', () => {
    expect(formatKpiValue(901742929.3, 'EUR')).toBe('901.742.929 €');
    expect(formatKpiValue(901742929.3, '')).toBe('901.742.929');
    expect(formatKpiValue(-4.7, '%')).toBe('-4,7%');
    expect(formatKpiValue(1.2, 'pp')).toBe('1,2 pp');
  });

  it('reads the unit from the catalog unit_format, not from the KPI ID (D-594)', () => {
    expect(unitFromFormat('percent_1')).toBe('%');
    expect(unitFromFormat('days_0')).toBe('d');
    expect(unitFromFormat('hours_0')).toBe('h');
    expect(unitFromFormat('minutes_1')).toBe('min');
    expect(unitFromFormat('eur_0')).toBe('');
    expect(unitFromFormat('ratio_1')).toBe('');
    expect(unitFromFormat(undefined)).toBe('');
    expect(isTimeOrCountFormat('days_1')).toBe(true);
    expect(isTimeOrCountFormat('count_0')).toBe(true);
    expect(isTimeOrCountFormat('percent_1')).toBe(false);
  });
});
