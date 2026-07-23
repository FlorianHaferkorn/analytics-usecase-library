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
  projectName: string;
  strategyAnchor: string;

  // Core artifacts
  brackets: UseCaseBracketV20Lean[];
  kpis: CatalogKpi[];
  actions: ActionDetail[];

  // Theme
  theme: ThemeConfig;

  // Aurora showcase (gold snapshot — not production SSOT)
  auroraLinked: boolean;
  auroraKpiCount: number;
  auroraSource: string | null;

  // Drift detection
  driftReport: DriftReport | null;
  driftLoading: boolean;

  // Notifications
  notifications: ActiveNotification[];

  // UI state
  selectedBracketId: string | null;
  activePanel: 'flow' | 'editor' | 'chat';
  isDirty: boolean;
  /** Global Forge domain filter (instant client-side; synced to ?domain= via replaceState). */
  domainFilter: string | null;

  // Wizard draft
  pendingWizardDraft: WizardDraft | null;
  setPendingWizardDraft: (draft: WizardDraft | null) => void;
  clearPendingWizardDraft: () => void;

  // Actions
  setProjectId: (id: string) => void;
  setProjectName: (name: string) => void;
  setStrategyAnchor: (anchor: string) => void;
  setBrackets: (brackets: UseCaseBracketV20Lean[]) => void;
  setKpis: (kpis: CatalogKpi[]) => void;
  setActions: (actions: ActionDetail[]) => void;
  setTheme: (theme: Partial<ThemeConfig>) => void;
  setAuroraBootstrap: (data: { linked: boolean; kpiCount: number; source: string | null }) => void;
  setDriftReport: (report: DriftReport | null) => void;
  setDriftLoading: (loading: boolean) => void;
  addNotification: (n: ActiveNotification) => void;
  dismissNotification: (id: string) => void;
  selectBracket: (id: string | null) => void;
  setActivePanel: (panel: 'flow' | 'editor' | 'chat') => void;
  setDomainFilter: (domain: string | null) => void;
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
  primary: '#2ECDE7',
  secondary: '#44B396',
  accent: '#2ECDE7',
  background: '#00396B',
  surface: '#004E7A',
  text: '#F5FBFC',
  fontFamily: 'Segoe UI',
  borderRadius: 4,
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

  auroraLinked: false,
  auroraKpiCount: 0,
  auroraSource: null,

  driftReport: null,
  driftLoading: false,

  notifications: [],

  selectedBracketId: null,
  activePanel: 'flow',
  isDirty: false,
  domainFilter: null,

  pendingWizardDraft: null,

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

  setAuroraBootstrap: ({ linked, kpiCount, source }) =>
    set({ auroraLinked: linked, auroraKpiCount: kpiCount, auroraSource: source }),

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
  setDomainFilter: (domainFilter) => set({ domainFilter }),

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
