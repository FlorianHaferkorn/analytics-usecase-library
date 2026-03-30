"use client";
import { useState } from "react";
import { useStudio } from "@/store/studio";
import { Button } from "@/components/ui/Button";
import type { Source } from "@/types/bracket";

let _srcCounter = 0;
function nextId() { return `src_${++_srcCounter}`; }

export function SourcesPane() {
  const { sources, addSource, removeSource, toggleSource, updateSourceContent } = useStudio();
  const [urlInput, setUrlInput] = useState("");
  const [textInput, setTextInput] = useState("");
  const [textName, setTextName] = useState("");
  const [fetching, setFetching] = useState(false);
  const [mode, setMode] = useState<"url" | "text">("url");

  async function handleAddUrl() {
    if (!urlInput.trim()) return;
    setFetching(true);
    try {
      const res = await fetch(`/api/fetch-url?url=${encodeURIComponent(urlInput)}`);
      const { text, title } = res.ok ? await res.json() : { text: "", title: urlInput };
      const src: Source = {
        id: nextId(),
        type: "url",
        name: title || urlInput,
        content: text || `[Could not fetch content from ${urlInput}]`,
        include_in_chat: true,
      };
      addSource(src);
      setUrlInput("");
    } finally {
      setFetching(false);
    }
  }

  function handleAddText() {
    if (!textInput.trim()) return;
    const src: Source = {
      id: nextId(),
      type: "text",
      name: textName || `Snippet ${sources.length + 1}`,
      content: textInput,
      include_in_chat: true,
    };
    addSource(src);
    setTextInput("");
    setTextName("");
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-3 py-2 border-b border-slate-200 shrink-0">
        <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Sources</h2>
        <p className="text-xs text-slate-400 mt-0.5">Ground the chat with documents or URLs</p>
      </div>

      {/* Add source */}
      <div className="px-3 py-2 border-b border-slate-100 shrink-0">
        <div className="flex gap-1 mb-2">
          {(["url", "text"] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`text-xs px-2 py-1 rounded cursor-pointer font-medium transition-colors
                ${mode === m ? "bg-slate-900 text-white" : "text-slate-500 hover:bg-slate-100"}`}
            >
              {m === "url" ? "URL" : "Paste text"}
            </button>
          ))}
        </div>

        {mode === "url" ? (
          <div className="flex gap-1">
            <input
              type="url"
              placeholder="https://..."
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAddUrl()}
              className="flex-1 text-xs border border-slate-200 rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-brand-primary"
            />
            <Button size="sm" onClick={handleAddUrl} loading={fetching} disabled={!urlInput.trim()}>
              Add
            </Button>
          </div>
        ) : (
          <div className="flex flex-col gap-1.5">
            <input
              type="text"
              placeholder="Source name…"
              value={textName}
              onChange={(e) => setTextName(e.target.value)}
              className="text-xs border border-slate-200 rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-brand-primary"
            />
            <textarea
              placeholder="Paste document text…"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              rows={4}
              className="text-xs border border-slate-200 rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-brand-primary resize-none"
            />
            <Button size="sm" onClick={handleAddText} disabled={!textInput.trim()}>
              Add
            </Button>
          </div>
        )}
      </div>

      {/* Source list */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-2">
        {sources.length === 0 && (
          <p className="text-xs text-slate-400 text-center mt-6">No sources yet</p>
        )}
        {sources.map((src) => (
          <div
            key={src.id}
            className={`rounded border text-xs p-2 transition-colors
              ${src.include_in_chat ? "border-brand-primary bg-blue-50" : "border-slate-200 bg-white"}`}
          >
            <div className="flex items-center gap-1.5 mb-1">
              <input
                type="checkbox"
                checked={src.include_in_chat}
                onChange={() => toggleSource(src.id)}
                className="accent-brand-primary"
              />
              <span className="font-medium text-slate-700 truncate flex-1" title={src.name}>
                {src.name}
              </span>
              <button
                onClick={() => removeSource(src.id)}
                className="text-slate-400 hover:text-red-500 ml-auto shrink-0 cursor-pointer"
                title="Remove"
              >
                ✕
              </button>
            </div>
            <p className="text-slate-400 line-clamp-2 pl-5">{src.content.slice(0, 120)}…</p>
          </div>
        ))}
      </div>
    </div>
  );
}
