import { describe, it, expect, beforeEach } from 'vitest';
import { useProjectStore, DEFAULT_THEME } from '@/lib/store/project-store';

describe('ProjectStore', () => {
  beforeEach(() => {
    // Reset store to initial state between tests
    useProjectStore.setState({
      projectId: 'default',
      projectName: 'Aurora Group',
      strategyAnchor: 'Profitable growth through margin quality, cash resilience & operational excellence',
      brackets: [],
      kpis: [],
      actions: [],
      theme: DEFAULT_THEME,
      driftReport: null,
      driftLoading: false,
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
    expect(state.theme.primary).toBe('#00D4AA');
  });

  it('setProjectName marks dirty', () => {
    useProjectStore.getState().setProjectName('New Corp');
    const state = useProjectStore.getState();
    expect(state.projectName).toBe('New Corp');
    expect(state.isDirty).toBe(true);
  });

  it('setStrategyAnchor marks dirty', () => {
    useProjectStore.getState().setStrategyAnchor('New anchor');
    expect(useProjectStore.getState().strategyAnchor).toBe('New anchor');
    expect(useProjectStore.getState().isDirty).toBe(true);
  });

  it('setBrackets does not mark dirty', () => {
    const bracket = { id: 'UC-001', title: 'Test' } as never;
    useProjectStore.getState().setBrackets([bracket]);
    expect(useProjectStore.getState().brackets).toHaveLength(1);
    expect(useProjectStore.getState().isDirty).toBe(false);
  });

  it('setTheme merges partial and marks dirty', () => {
    useProjectStore.getState().setTheme({ primary: '#FF0000', borderRadius: 16 });
    const theme = useProjectStore.getState().theme;
    expect(theme.primary).toBe('#FF0000');
    expect(theme.borderRadius).toBe(16);
    // Other values preserved
    expect(theme.secondary).toBe(DEFAULT_THEME.secondary);
    expect(useProjectStore.getState().isDirty).toBe(true);
  });

  it('updateBracket updates the correct bracket immutably', () => {
    const b1 = { id: 'UC-001', title: 'First' } as never;
    const b2 = { id: 'UC-002', title: 'Second' } as never;
    useProjectStore.getState().setBrackets([b1, b2]);

    useProjectStore.getState().updateBracket('UC-001', { title: 'Updated First' } as never);
    const brackets = useProjectStore.getState().brackets;
    expect(brackets[0].title).toBe('Updated First');
    expect(brackets[1].title).toBe('Second');
    expect(useProjectStore.getState().isDirty).toBe(true);
  });

  it('selectBracket and setActivePanel update UI state', () => {
    useProjectStore.getState().selectBracket('UC-005');
    expect(useProjectStore.getState().selectedBracketId).toBe('UC-005');

    useProjectStore.getState().setActivePanel('editor');
    expect(useProjectStore.getState().activePanel).toBe('editor');
  });

  it('markClean resets isDirty', () => {
    useProjectStore.getState().setProjectName('Dirty');
    expect(useProjectStore.getState().isDirty).toBe(true);
    useProjectStore.getState().markClean();
    expect(useProjectStore.getState().isDirty).toBe(false);
  });
});
