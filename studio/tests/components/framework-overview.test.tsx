import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { FrameworkOverview } from '@/components/ui/framework-overview';

const stats = { kpiCount: 20, bracketCount: 4, actionCount: 8, pendingReviews: 0, certified: 10, inReview: 0, totalDomains: 2, golden20Present: 20, golden20Total: 20, orphanActions: 0 };

describe('Library overview hierarchy and scope', () => {
  it('does not present library counts as project readiness', () => {
    render(<FrameworkOverview stats={stats} domains={[]} topKpis={[]} />);
    expect(screen.getByText(/not the selected project’s progress or readiness/)).toBeTruthy();
    expect(screen.queryByText('Ready')).toBeNull();
    expect(screen.queryByText(/framework v1.0.0/)).toBeNull();
    const recommendation = screen.getByRole('heading', { name: 'Explore a use-case blueprint' });
    const metrics = screen.getByText('KPIs', { exact: true });
    expect(recommendation.compareDocumentPosition(metrics) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    const disclosure = screen.getByText('Library composition and KPI examples').closest('details');
    expect(disclosure?.open).toBe(false);
  });

  it('prioritizes reported errors over reviews and avoids false clean-state text', () => {
    render(<FrameworkOverview stats={{ ...stats, pendingReviews: 2 }} domains={[]} topKpis={[]} drift={{ errorCount: 3, warningCount: 1, topIssues: [] }} />);
    expect(screen.getByRole('heading', { name: 'Review framework drift' })).toBeTruthy();
    expect(screen.queryByText('References are consistent')).toBeNull();
    expect(screen.getByText(/report contains findings/)).toBeTruthy();
  });

  it('labels the certified fraction accurately rather than documentation coverage', () => {
    render(<FrameworkOverview stats={stats} domains={[]} topKpis={[]} />);
    expect(screen.getByRole('img', { name: '50% of library KPIs certified', hidden: true })).toBeTruthy();
    expect(screen.queryByText(/Documentation/)).toBeNull();
  });
});
