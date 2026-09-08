import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { StudioFormField, StudioInput, StudioSelectionItem, StudioTable, StudioTableHeadCell, StudioTableShell } from '@/components/ui/studio-data';
import { CollapsiblePanel } from '@/components/ui/collapsible-panel';
import { NotificationBell } from '@/components/notifications/notification-bell';
import { KBD, Pill } from '@/components/ui/badges';

afterEach(cleanup);

describe('Migrated legacy primitives', () => {
  it('associates the form-field label and preserves the native input focus style', () => {
    render(<StudioFormField label="Name"><StudioInput id="name" /></StudioFormField>);
    const input = screen.getByRole('textbox', { name: 'Name' });
    expect(input.id).toBe('name');
    expect(input.style.outline).not.toBe('none');
    expect(input.style.fontSize).toBe('var(--text-sm)');
  });

  it('exposes row-selection state without an interactive input nested inside a button', () => {
    const select = vi.fn();
    render(<StudioSelectionItem selected onClick={select} primary="Revenue" secondary="Monthly sales" />);
    const button = screen.getByRole('button', { name: /Revenue/ });
    expect(button.getAttribute('aria-pressed')).toBe('true');
    expect(button.querySelector('input')).toBeNull();
    fireEvent.click(button);
    expect(select).toHaveBeenCalledOnce();
  });

  it('retains readable table headers and horizontal access to wide tables', () => {
    const { container } = render(<StudioTableShell><StudioTable><thead><tr><StudioTableHeadCell>Owner</StudioTableHeadCell></tr></thead></StudioTable></StudioTableShell>);
    const heading = screen.getByRole('columnheader', { name: 'Owner' });
    expect(heading.getAttribute('scope')).toBe('col');
    expect(heading.style.fontSize).toBe('var(--text-xs)');
    expect((container.firstChild as HTMLElement).style.overflowX).toBe('auto');
  });

  it('exposes the native disclosure button state and its controlled content', () => {
    render(<CollapsiblePanel title="Assumptions">Evidence</CollapsiblePanel>);
    const collapse = screen.getByRole('button', { name: 'Collapse Assumptions' });
    const id = collapse.getAttribute('aria-controls')!;
    expect(collapse.getAttribute('aria-expanded')).toBe('true');
    fireEvent.click(collapse);
    expect(screen.getByRole('button', { name: 'Expand Assumptions' }).getAttribute('aria-expanded')).toBe('false');
    expect(document.getElementById(id)?.hidden).toBe(true);
  });

  it('names the notification action even when no count is present', () => {
    const { rerender } = render(<NotificationBell count={0} onClick={() => {}} />);
    expect(screen.getByRole('button', { name: 'Notifications' })).toBeDefined();
    rerender(<NotificationBell count={42} onClick={() => {}} />);
    expect(screen.getByRole('button', { name: 'Notifications, 42 unread' })).toBeDefined();
    expect(screen.getByText('9+').style.fontSize).toBe('var(--text-xs)');
  });

  it('uses theme-aware status tokens and readable shortcut labels', () => {
    render(<><Pill tone="positive">Accepted</Pill><KBD>Ctrl K</KBD></>);
    expect(screen.getByText('Accepted').style.color).toBe('var(--positive-fg)');
    expect(screen.getByText('Ctrl K').style.fontSize).toBe('var(--text-xs)');
  });
});
