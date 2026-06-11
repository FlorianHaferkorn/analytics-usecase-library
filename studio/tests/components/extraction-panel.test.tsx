import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ExtractionPanel, type ExtractedElement } from '@/components/discovery/extraction-panel';

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), prefetch: vi.fn() }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}));

// --- Helper to build AI-like response text ---
function kpiResponse(id: string, name: string, sourceHint?: string): string {
  const src = sourceHint ? `Source: ${sourceHint}\n` : '';
  return `${src}kpi_id: "${id}"\nname: "${name}"\npurpose: "tracks performance"`;
}

function actionResponse(id: string, name: string): string {
  return `action_id: "${id}"\nname: "${name}"\ndescription: "some action"`;
}

function anchorResponse(label: string): string {
  return `Strategy anchor: "${label}"`;
}

describe('ExtractionPanel', () => {
  it('renders empty state when no response', () => {
    render(<ExtractionPanel lastResponse="" sourceNames={[]} />);
    expect(screen.getByText(/will appear here/i)).toBeTruthy();
  });

  it('extracts KPI elements from response text', () => {
    const text = kpiResponse('KPI-001', 'Revenue Growth');
    render(<ExtractionPanel lastResponse={text} sourceNames={[]} />);
    expect(screen.getByText('Revenue Growth')).toBeTruthy();
    expect(screen.getByText('KPI-001')).toBeTruthy();
  });

  it('extracts Action elements from response text', () => {
    const text = actionResponse('ACT-010', 'Reprice Slow Movers');
    render(<ExtractionPanel lastResponse={text} sourceNames={[]} />);
    expect(screen.getByText('Reprice Slow Movers')).toBeTruthy();
    expect(screen.getByText('ACT-010')).toBeTruthy();
  });

  it('extracts Strategy Anchors from response text', () => {
    const text = anchorResponse('Profitable growth through margin quality');
    render(<ExtractionPanel lastResponse={text} sourceNames={[]} />);
    expect(screen.getByText('Profitable growth through margin quality')).toBeTruthy();
  });

  it('shows correct count in All filter button', () => {
    const text = [
      kpiResponse('KPI-001', 'Rev Growth'),
      actionResponse('ACT-001', 'Reprice'),
    ].join('\n\n');
    render(<ExtractionPanel lastResponse={text} sourceNames={[]} />);
    expect(screen.getByText('All (2)')).toBeTruthy();
  });

  it('filters by element type', () => {
    const text = [
      kpiResponse('KPI-001', 'Rev Growth'),
      actionResponse('ACT-001', 'Reprice Items'),
    ].join('\n\n');
    render(<ExtractionPanel lastResponse={text} sourceNames={[]} />);

    // Click KPIs filter
    fireEvent.click(screen.getByText('KPIs'));
    expect(screen.getByText('Rev Growth')).toBeTruthy();
    expect(screen.queryByText('Reprice Items')).toBeNull();

    // Click Actions filter
    fireEvent.click(screen.getByText('Actions'));
    expect(screen.queryByText('Rev Growth')).toBeNull();
    expect(screen.getByText('Reprice Items')).toBeTruthy();
  });

  it('attributes source when source name appears in context', () => {
    const text = `Based on the Annual Report 2024 data:\nkpi_id: "KPI-042"\nname: "Cash Conversion Cycle"`;
    render(<ExtractionPanel lastResponse={text} sourceNames={['Annual Report 2024']} />);
    expect(screen.getByText('Annual Report 2024')).toBeTruthy();
  });

  it('expands element to show traced source on click', () => {
    const text = `Source: Strategy Document\nkpi_id: "KPI-007"\nname: "EBIT Margin"`;
    render(<ExtractionPanel lastResponse={text} sourceNames={[]} />);

    // Click to expand
    fireEvent.click(screen.getByText('EBIT Margin'));
    // Should show the "Traced to:" section with the source
    expect(screen.getByText('Traced to:')).toBeTruthy();
  });

  it('shows Draft-Branch button when elements exist', () => {
    const text = kpiResponse('KPI-001', 'Revenue');
    render(<ExtractionPanel lastResponse={text} sourceNames={[]} />);
    expect(screen.getByText('Create draft branch')).toBeTruthy();
  });

  it('does not show Draft-Branch button when no elements', () => {
    render(<ExtractionPanel lastResponse="no structured data here" sourceNames={[]} />);
    expect(screen.queryByText('Create draft branch')).toBeNull();
  });
});
