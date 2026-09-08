import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { useState } from 'react';
import { StudioButton, StudioField, StudioSegmentedControl } from '@/components/ui/studio-page';
import { StudioSelect } from '@/components/ui/studio-data';

afterEach(cleanup);

describe('Studio page primitives', () => {
  it('defaults buttons to non-submit and forwards native attributes', () => {
    const submit = vi.fn((event) => event.preventDefault());
    render(<form onSubmit={submit}><StudioButton aria-label="Refresh data" title="Refresh" tone="info">Refresh</StudioButton></form>);
    const button = screen.getByRole('button', { name: 'Refresh data' });
    fireEvent.click(button);
    expect(submit).not.toHaveBeenCalled();
    expect(button.getAttribute('type')).toBe('button');
    expect(button.getAttribute('data-tone')).toBe('info');
    expect(button.getAttribute('title')).toBe('Refresh');
  });

  it('allows an explicitly requested submit button', () => {
    const submit = vi.fn((event) => event.preventDefault());
    render(<form onSubmit={submit}><StudioButton type="submit">Save</StudioButton></form>);
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));
    expect(submit).toHaveBeenCalledOnce();
  });

  it('associates fields with native and wrapped inputs, preserving supplied IDs', () => {
    render(<><StudioField label="Project"><StudioSelect id="project-select"><option>Aurora</option></StudioSelect></StudioField><StudioField label="Description"><input /></StudioField></>);
    expect(screen.getByLabelText('Project').id).toBe('project-select');
    expect(screen.getByLabelText('Description').tagName).toBe('INPUT');
  });

  it('labels grouped options and supports arrows, Home, End and pressed state', () => {
    function Example() {
      const [value, setValue] = useState('flow');
      return <StudioField label="Workspace mode"><StudioSegmentedControl value={value} onChange={setValue} tone="success" options={[{ value: 'flow', label: 'Flow' }, { value: 'split', label: 'Flow and YAML' }, { value: 'yaml', label: 'YAML' }]} /></StudioField>;
    }
    render(<Example />);
    const group = screen.getByRole('group', { name: 'Workspace mode' });
    const flow = screen.getByRole('button', { name: 'Flow' });
    const split = screen.getByRole('button', { name: 'Flow and YAML' });
    const yaml = screen.getByRole('button', { name: 'YAML' });
    expect(group.getAttribute('data-tone')).toBe('success');
    expect(flow.tabIndex).toBe(0);
    fireEvent.keyDown(flow, { key: 'ArrowRight' });
    expect(split.getAttribute('aria-pressed')).toBe('true');
    expect(document.activeElement).toBe(split);
    expect(flow.tabIndex).toBe(-1);
    fireEvent.keyDown(split, { key: 'End' });
    expect(document.activeElement).toBe(yaml);
    fireEvent.keyDown(yaml, { key: 'ArrowRight' });
    expect(document.activeElement).toBe(flow);
    fireEvent.keyDown(flow, { key: 'End' });
    fireEvent.keyDown(yaml, { key: 'Home' });
    expect(document.activeElement).toBe(flow);
  });
});
