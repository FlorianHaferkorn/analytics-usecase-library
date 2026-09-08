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
import type { DriftReport } from '@/lib/validation/drift-scanner';
import type { ActiveNotification } from '@/lib/notifications/rule-types';
import type { AuroraBootstrapData } from '@/lib/aurora/bootstrap-data';

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
  fontWeight?: number;
  lineHeight?: number;
  letterSpacing?: number;
  shadow?: string;
}

/** Project-level state. */
export interface ProjectState {
  // Meta
  projectId: string;
  dataScope: 'library' | 'project';
  packageRevisionHash: string | null;
  projectName: string;
  strategyAnchor: string;

  // Core artifacts
  brackets: UseCaseBracketV20Lean[];
  kpis: CatalogKpi[];
  actions: ActionDetail[];

  // Theme
  theme: ThemeConfig;

  // Aurora showcase snapshot, bootstrapped server-side (see lib/aurora/bootstrap-data)
  aurora: AuroraBootstrapData;

  // Drift detection
  driftReport: DriftReport | null;
  driftLoading: boolean;

  // Notifications
  notifications: ActiveNotification[];

  // Cross-surface domain filter (owned here so sidebar, URL and every page agree)
  domainFilter: string | null;

  // UI state
  selectedBracketId: string | null;
  activePanel: 'flow' | 'editor' | 'chat';
  isDirty: boolean;

  // Wizard draft
  pendingWizardDraft: WizardDraft | null;
  setPendingWizardDraft: (draft: WizardDraft | null) => void;
  clearPendingWizardDraft: () => void;

  // Actions
  setProjectId: (id: string) => void;
  setDataScope: (scope: 'library' | 'project') => void;
  setPackageRevisionHash: (hash: string | null) => void;
  setProjectName: (name: string) => void;
  setStrategyAnchor: (anchor: string) => void;
  setBrackets: (brackets: UseCaseBracketV20Lean[]) => void;
  setKpis: (kpis: CatalogKpi[]) => void;
  setActions: (actions: ActionDetail[]) => void;
  setTheme: (theme: Partial<ThemeConfig>) => void;
  setAurora: (aurora: AuroraBootstrapData) => void;
  setDomainFilter: (name: string | null) => void;
  setDriftReport: (report: DriftReport | null) => void;
  setDriftLoading: (loading: boolean) => void;
  addNotification: (n: ActiveNotification) => void;
  dismissNotification: (id: string) => void;
  selectBracket: (id: string | null) => void;
  setActivePanel: (panel: 'flow' | 'editor' | 'chat') => void;
  updateBracket: (id: string, update: Partial<UseCaseBracketV20Lean>) => void;
  markClean: () => void;
}

export type WizardDraftKind = 'kpi' | 'bracket' | 'action' | 'source';

export interface WizardDraft {
  kind: WizardDraftKind;
  name: string;
  ref: string;
  domain: string;
  type: string;
  grain: string;
  description: string;
  sql?: string;
  createdAt: string;
}

export const DEFAULT_THEME: ThemeConfig = {
  primary: '#0078D4',
  secondary: '#50E6FF',
  accent: '#0078D4',
  background: '#F5F5F5',
  surface: '#FFFFFF',
  text: '#201F1E',
  fontFamily: 'Segoe UI',
  borderRadius: 8,
};

export const useProjectStore = create<ProjectState>((set) => ({
  projectId: 'default',
  dataScope: 'library',
  packageRevisionHash: null,
  projectName: 'Aurora Group',
  strategyAnchor:
    'Profitable growth through margin quality, cash resilience & operational excellence',

  brackets: [],
  kpis: [],
  actions: [],

  theme: DEFAULT_THEME,

  // Unlinked until the shell bootstraps a snapshot — surfaces fall back to their stubs.
  aurora: { kpis: {}, linked: false, generatedAt: null, source: null },

  domainFilter: null,

  driftReport: null,
  driftLoading: false,

  notifications: [],

  selectedBracketId: null,
  activePanel: 'flow',
  isDirty: false,

  pendingWizardDraft: null,

  setProjectId: (id) => set((state) => id === state.projectId ? {} : ({
    projectId: id, dataScope: 'project', packageRevisionHash: null,
    projectName: id, strategyAnchor: '', brackets: [], kpis: [], actions: [],
    theme: DEFAULT_THEME, aurora: { kpis: {}, linked: false, generatedAt: null, source: null },
    driftReport: null, driftLoading: false, notifications: [], domainFilter: null,
    selectedBracketId: null, pendingWizardDraft: null, activePanel: 'flow', isDirty: false,
  })),
  setDataScope: (dataScope) => set({ dataScope }),
  setPackageRevisionHash: (packageRevisionHash) => set({ packageRevisionHash }),
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

  // Server-bootstrapped, not user-authored — deliberately does not set isDirty.
  setAurora: (aurora) => set({ aurora }),

  // A view filter, not project content — likewise never marks the project dirty.
  setDomainFilter: (name) => set({ domainFilter: name }),

  setDriftReport: (report) => set({ driftReport: report }),
  setDriftLoading: (loading) => set({ driftLoading: loading }),

  addNotification: (n) =>
    set((state) => ({ notifications: [...state.notifications, n] })),
  dismissNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.map((n) =>
        n.id === id ? { ...n, dismissed: true } : n,
      ),
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

  setPendingWizardDraft: (pendingWizardDraft) => set({ pendingWizardDraft }),
  clearPendingWizardDraft: () => set({ pendingWizardDraft: null }),
}));
