"use client";
import { useEffect } from "react";
import { useStudio } from "@/store/studio";
import { SourcesPane } from "@/components/studio/SourcesPane";
import { ChatPane } from "@/components/studio/ChatPane";
import { LivingTree } from "@/components/studio/LivingTree";
import { YamlEditor } from "@/components/studio/YamlEditor";

export default function StudioPage() {
  const { setRegistry, setRegistryLoading, setRegistryError, activeTab, setActiveTab } =
    useStudio();

  useEffect(() => {
    setRegistryLoading(true);
    fetch("/api/registry")
      .then((r) => r.json())
      .then((d) => {
        if (d.error) setRegistryError(d.error);
        else setRegistry(d);
      })
      .catch((e) => setRegistryError(e.message))
      .finally(() => setRegistryLoading(false));
  }, [setRegistry, setRegistryLoading, setRegistryError]);

  return (
    <div className="h-full flex overflow-hidden">
      {/* Left: Sources */}
      <div className="w-56 shrink-0 border-r border-theme bg-theme flex flex-col overflow-hidden">
        <SourcesPane />
      </div>

      {/* Center: Chat */}
      <div className="flex-1 border-r border-theme bg-theme-secondary flex flex-col overflow-hidden min-w-0">
        <ChatPane />
      </div>

      {/* Right: Studio pane */}
      <div className="w-[480px] shrink-0 bg-theme flex flex-col overflow-hidden">
        <div className="border-b border-theme flex items-center px-3 shrink-0">
          {(["tree", "yaml"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setActiveTab(t)}
              className={`px-4 py-2.5 text-xs font-semibold uppercase tracking-wider border-b-2 transition-colors cursor-pointer
                ${activeTab === t
                  ? "border-brand-mint text-brand-mint"
                  : "border-transparent text-theme-tertiary hover:text-theme-secondary"
                }`}
            >
              {t === "tree" ? "Living Tree" : "YAML Editor"}
            </button>
          ))}
        </div>
        <div className="flex-1 overflow-hidden">
          {activeTab === "tree" ? <LivingTree /> : <YamlEditor />}
        </div>
      </div>
    </div>
  );
}
