import { fireEvent, render, screen } from '@testing-library/react';
import { expect, it } from 'vitest';
import { ProjectReleasePanel } from '@/components/delivery/project-release-panel';

it('requires rationale and explicit input-only confirmation before requesting approval', () => {
  render(<ProjectReleasePanel projectId="project_demo" revisionHash={'a'.repeat(64)} dirty={false} />);
  const attest = screen.getByRole('button', { name: 'Attest and download inputs' }) as HTMLButtonElement;
  expect(attest.disabled).toBe(true);
  fireEvent.change(screen.getByLabelText('Input release rationale'), { target: { value: 'Reviewed exact inputs against the project evidence.' } });
  expect(attest.disabled).toBe(true);
  fireEvent.click(screen.getByRole('checkbox'));
  expect(attest.disabled).toBe(false);
  expect(screen.getByText(/No Fabric deployment artifacts/)).toBeTruthy();
});

it('cannot release unsaved changes even when the user checked confirmation', () => {
  render(<ProjectReleasePanel projectId="project_demo" revisionHash={'b'.repeat(64)} dirty />);
  fireEvent.change(screen.getByLabelText('Input release rationale'), { target: { value: 'Reviewed exact inputs against the project evidence.' } });
  fireEvent.click(screen.getByRole('checkbox'));
  expect((screen.getByRole('button', { name: 'Attest and download inputs' }) as HTMLButtonElement).disabled).toBe(true);
  expect((screen.getByRole('button', { name: 'Download existing release' }) as HTMLButtonElement).disabled).toBe(true);
  expect(screen.getByRole('status').textContent).toContain('Save and review');
});
