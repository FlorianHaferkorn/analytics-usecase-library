"use client";
import { create } from "zustand";
import type { UseCaseDraft, ChatMessage, Source } from "@/types/bracket";
import type { Registry } from "@/types/registry";
import { EMPTY_DRAFT, draftToYaml, yamlToDraft } from "@/lib/bracket";

// Re-export for convenience
export { draftToYaml, yamlToDraft };

interface StudioState {
  // Registry
  registry: Registry | null;
  registryLoading: boolean;
  registryError: string | null;
  setRegistry: (r: Registry) => void;
  setRegistryLoading: (v: boolean) => void;
  setRegistryError: (e: string | null) => void;

  // Active use case draft
  draft: UseCaseDraft;
  yamlText: string;
  setDraft: (d: UseCaseDraft) => void;
  setYamlText: (t: string) => void;
  syncYamlFromDraft: () => void;
  syncDraftFromYaml: () => string | null; // returns parse error or null

  // Sources
  sources: Source[];
  addSource: (s: Source) => void;
  removeSource: (id: string) => void;
  toggleSource: (id: string) => void;
  updateSourceContent: (id: string, content: string) => void;

  // Chat
  messages: ChatMessage[];
  chatLoading: boolean;
  addMessage: (m: ChatMessage) => void;
  setChatLoading: (v: boolean) => void;
  clearChat: () => void;

  // UI state
  activeTab: "tree" | "yaml";
  setActiveTab: (t: "tree" | "yaml") => void;
}

export const useStudio = create<StudioState>((set, get) => ({
  registry: null,
  registryLoading: false,
  registryError: null,
  setRegistry: (r) => set({ registry: r }),
  setRegistryLoading: (v) => set({ registryLoading: v }),
  setRegistryError: (e) => set({ registryError: e }),

  draft: EMPTY_DRAFT,
  yamlText: draftToYaml(EMPTY_DRAFT),
  setDraft: (d) => set({ draft: d }),
  setYamlText: (t) => set({ yamlText: t }),
  syncYamlFromDraft: () => set((s) => ({ yamlText: draftToYaml(s.draft) })),
  syncDraftFromYaml: () => {
    try {
      const d = yamlToDraft(get().yamlText);
      set({ draft: d });
      return null;
    } catch (e) {
      return e instanceof Error ? e.message : "Parse error";
    }
  },

  sources: [],
  addSource: (s) => set((st) => ({ sources: [...st.sources, s] })),
  removeSource: (id) => set((st) => ({ sources: st.sources.filter((s) => s.id !== id) })),
  toggleSource: (id) =>
    set((st) => ({
      sources: st.sources.map((s) =>
        s.id === id ? { ...s, include_in_chat: !s.include_in_chat } : s
      ),
    })),
  updateSourceContent: (id, content) =>
    set((st) => ({
      sources: st.sources.map((s) => (s.id === id ? { ...s, content } : s)),
    })),

  messages: [],
  chatLoading: false,
  addMessage: (m) => set((st) => ({ messages: [...st.messages, m] })),
  setChatLoading: (v) => set({ chatLoading: v }),
  clearChat: () => set({ messages: [] }),

  activeTab: "tree",
  setActiveTab: (t) => set({ activeTab: t }),
}));
