import { describe, it, expect, beforeEach } from 'vitest';
import { useProjectStore } from '@/lib/store/project-store';

describe('useProjectStore', () => {
  beforeEach(() => {
    // Reset store to initial state
    useProjectStore.setState({
      projectName: 'Aurora Group',
      strategyAnchor:
        'Profitable growth through margin quality, cash resilience & operational excellence',
      brackets: [],
      kpis: [],
      actions: [],
      selectedBracketId: null,
      activePanel: 'flow',
      isDirty: false,
    });
  });

  it('has correct initial state', () => {
    const state = useProjectStore.getState();
    expect(state.projectName).toBe('Aurora Group');
    expect(state.isDirty).toBe(false);
    expect(state.activePanel).toBe('flow');
  });

  it('setProjectName updates name and marks dirty', () => {
    useProjectStore.getState().setProjectName('New Corp');
    const state = useProjectStore.getState();
    expect(state.projectName).toBe('New Corp');
    expect(state.isDirty).toBe(true);
  });

  it('selectBracket updates selectedBracketId', () => {
    useProjectStore.getState().selectBracket('UC001');
    expect(useProjectStore.getState().selectedBracketId).toBe('UC001');
  });

  it('setTheme merges partial theme', () => {
    useProjectStore.getState().setTheme({ primary: '#FF0000' });
    const theme = useProjectStore.getState().theme;
    expect(theme.primary).toBe('#FF0000');
    expect(theme.secondary).toBe('#50E6FF'); // unchanged governed default
    expect(useProjectStore.getState().isDirty).toBe(true);
  });

  it('updateBracket updates a specific bracket', () => {
    const bracket = {
      id: 'UC001',
      title: 'Original',
      domain: 'Finance',
      schema_version: '2.0',
      orchestration: {
        strategic_kpi_id: 'K1',
        influencing_kpi_ids: [],
        supporting_kpi_ids: [],
        action_code_ids: [],
      },
    } as never;

    useProjectStore.getState().setBrackets([bracket]);
    useProjectStore.getState().updateBracket('UC001', { title: 'Updated' } as never);

    const updated = useProjectStore.getState().brackets[0];
    expect((updated as { title: string }).title).toBe('Updated');
    expect(useProjectStore.getState().isDirty).toBe(true);
  });

  it('markClean resets isDirty', () => {
    useProjectStore.getState().setProjectName('Dirty');
    expect(useProjectStore.getState().isDirty).toBe(true);
    useProjectStore.getState().markClean();
    expect(useProjectStore.getState().isDirty).toBe(false);
  });

  it('setActivePanel changes panel', () => {
    useProjectStore.getState().setActivePanel('editor');
    expect(useProjectStore.getState().activePanel).toBe('editor');
  });
});
