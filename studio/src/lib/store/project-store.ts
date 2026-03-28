/**
 * Project Store — Central state for bi-directional sync.
 *
 * All UI surfaces (Flow Tree, YAML Editor, Chat) read from and write to
 * this single Zustand store. Changes propagate automatically.
 *
 * Sync rule: Chat → Store → Tree + YAML
 *            Tree → Store → YAML + Chat context
 *            YAML → Store → Tree + Chat context
 */

import { create } from 'zustand';
import type { UseCaseBracketV20Lean } from '@/lib/schemas';
import type { CatalogKpi } from '@/lib/core/catalog-loader';

/** Serializable action detail for the flow. */
export interface ActionDetail {
  id: string;
  name: string;
  status: string;
  domain: string;
  triggerKpis: string[];
  guardrailKpis: string[];
  outcomeKpis: string[];
}

/** Theme configuration for the Brand Lab. */
export interface ThemeConfig {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  surface: string;
  text: string;
  fontFamily: string;
  borderRadius: number;
}

/** Project-level state. */
export interface ProjectState {
  // Meta
  projectId: string;
  projectName: string;
  strategyAnchor: string;

  // Core artifacts
  brackets: UseCaseBracketV20Lean[];
  kpis: CatalogKpi[];
  actions: ActionDetail[];

  // Theme
  theme: ThemeConfig;

  // UI state
  selectedBracketId: string | null;
  activePanel: 'flow' | 'editor' | 'chat';
  isDirty: boolean;

  // Actions
  setProjectId: (id: string) => void;
  setProjectName: (name: string) => void;
  setStrategyAnchor: (anchor: string) => void;
  setBrackets: (brackets: UseCaseBracketV20Lean[]) => void;
  setKpis: (kpis: CatalogKpi[]) => void;
  setActions: (actions: ActionDetail[]) => void;
  setTheme: (theme: Partial<ThemeConfig>) => void;
  selectBracket: (id: string | null) => void;
  setActivePanel: (panel: 'flow' | 'editor' | 'chat') => void;
  updateBracket: (id: string, update: Partial<UseCaseBracketV20Lean>) => void;
  markClean: () => void;
}

export const DEFAULT_THEME: ThemeConfig = {
  primary: '#00D4AA',
  secondary: '#FFB800',
  accent: '#3B82F6',
  background: '#1E293B',
  surface: '#0F172A',
  text: '#F1F5F9',
  fontFamily: 'Inter',
  borderRadius: 8,
};

export const useProjectStore = create<ProjectState>((set) => ({
  projectId: 'default',
  projectName: 'Aurora Group',
  strategyAnchor:
    'Profitable growth through margin quality, cash resilience & operational excellence',

  brackets: [],
  kpis: [],
  actions: [],

  theme: DEFAULT_THEME,

  selectedBracketId: null,
  activePanel: 'flow',
  isDirty: false,

  setProjectId: (id) => set({ projectId: id, isDirty: false }),
  setProjectName: (name) => set({ projectName: name, isDirty: true }),
  setStrategyAnchor: (anchor) => set({ strategyAnchor: anchor, isDirty: true }),
  setBrackets: (brackets) => set({ brackets }),
  setKpis: (kpis) => set({ kpis }),
  setActions: (actions) => set({ actions }),

  setTheme: (partial) =>
    set((state) => ({
      theme: { ...state.theme, ...partial },
      isDirty: true,
    })),

  selectBracket: (id) => set({ selectedBracketId: id }),
  setActivePanel: (panel) => set({ activePanel: panel }),

  updateBracket: (id, update) =>
    set((state) => ({
      brackets: state.brackets.map((b) =>
        b.id === id ? { ...b, ...update } : b
      ),
      isDirty: true,
    })),

  markClean: () => set({ isDirty: false }),
}));
