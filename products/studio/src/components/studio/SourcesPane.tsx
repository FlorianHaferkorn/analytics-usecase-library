"use client";
import { useState, useRef } from "react";
import { useStudio } from "@/store/studio";
import { Button } from "@/components/ui/Button";
import type { Source } from "@/types/bracket";

let _srcCounter = 0;
function nextId() { return `src_${++_srcCounter}`; }

export function SourcesPane() {
  const { sources, addSource, removeSource, toggleSource } = useStudio();
  const [urlInput, setUrlInput] = useState("");
  const [textInput, setTextInput] = useState("");
  const [textName, setTextName] = useState("");
  const [fetching, setFetching] = useState(false);
  const [mode, setMode] = useState<"url" | "text" | "file">("url");
  const fileRef = useRef<HTMLInputElement>(null);

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

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const files = e.target.files;
    if (!files) return;
    for (const file of Array.from(files)) {
      try {
        const text = await file.text();
        const src: Source = {
          id: nextId(),
          type: "text",
          name: file.name,
          content: text.slice(0, 50000),
          include_in_chat: true,
        };
        addSource(src);
      } catch {
        const src: Source = {
          id: nextId(),
          type: "text",
          name: file.name,
          content: `[Could not read file: ${file.name}]`,
          include_in_chat: false,
        };
        addSource(src);
      }
    }
    if (fileRef.current) fileRef.current.value = "";
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-3 py-2 border-b border-theme shrink-0">
        <h2 className="text-xs font-semibold text-theme-tertiary uppercase tracking-wider">Sources</h2>
        <p className="text-[10px] text-theme-tertiary mt-0.5">Ground the chat with documents or URLs</p>
      </div>

      {/* Add source */}
      <div className="px-3 py-2 border-b border-theme shrink-0">
        <div className="flex gap-0.5 mb-2">
          {(["url", "text", "file"] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`text-[10px] px-2 py-1 rounded cursor-pointer font-medium transition-colors
                ${mode === m ? "bg-brand-mint text-brand-petrol" : "text-theme-tertiary hover:bg-theme-tertiary"}`}
            >
              {m === "url" ? "URL" : m === "text" ? "Paste" : "Upload"}
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
              className="flex-1 text-xs bg-theme-secondary border border-theme rounded px-2 py-1.5 text-theme focus:outline-none focus:ring-1 focus:ring-brand-mint placeholder:text-theme-tertiary"
            />
            <Button size="sm" onClick={handleAddUrl} loading={fetching} disabled={!urlInput.trim()}>
              Add
            </Button>
          </div>
        ) : mode === "text" ? (
          <div className="flex flex-col gap-1.5">
            <input
              type="text"
              placeholder="Source name..."
              value={textName}
              onChange={(e) => setTextName(e.target.value)}
              className="text-xs bg-theme-secondary border border-theme rounded px-2 py-1.5 text-theme focus:outline-none focus:ring-1 focus:ring-brand-mint placeholder:text-theme-tertiary"
            />
            <textarea
              placeholder="Paste document text..."
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              rows={3}
              className="text-xs bg-theme-secondary border border-theme rounded px-2 py-1.5 text-theme focus:outline-none focus:ring-1 focus:ring-brand-mint resize-none placeholder:text-theme-tertiary"
            />
            <Button size="sm" onClick={handleAddText} disabled={!textInput.trim()}>
              Add
            </Button>
          </div>
        ) : (
          <div>
            <input
              ref={fileRef}
              type="file"
              multiple
              accept=".txt,.md,.yaml,.yml,.json,.csv,.tsv,.xml,.html,.pdf"
              onChange={handleFileUpload}
              className="hidden"
            />
            <button
              onClick={() => fileRef.current?.click()}
              className="w-full border-2 border-dashed border-theme rounded-md py-4 text-center cursor-pointer hover:border-brand-mint transition-colors"
            >
              <div className="text-xs text-theme-tertiary">
                Click to upload files
              </div>
              <div className="text-[10px] text-theme-tertiary mt-1">
                .txt .md .yaml .json .csv .xml
              </div>
            </button>
          </div>
        )}
      </div>

      {/* Source list */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1.5">
        {sources.length === 0 && (
          <p className="text-xs text-theme-tertiary text-center mt-6">No sources yet</p>
        )}
        {sources.map((src) => (
          <div
            key={src.id}
            className={`rounded border text-xs p-2 transition-colors
              ${src.include_in_chat ? "border-brand-mint/40 bg-brand-mint/5" : "border-theme bg-theme"}`}
          >
            <div className="flex items-center gap-1.5 mb-0.5">
              <input
                type="checkbox"
                checked={src.include_in_chat}
                onChange={() => toggleSource(src.id)}
                className="accent-brand-mint"
              />
              <span className="font-medium text-theme text-[10px] truncate flex-1" title={src.name}>
                {src.name}
              </span>
              <button
                onClick={() => removeSource(src.id)}
                className="text-theme-tertiary hover:text-signal-negative ml-auto shrink-0 cursor-pointer"
                title="Remove"
              >
                &times;
              </button>
            </div>
            <p className="text-theme-tertiary line-clamp-1 pl-5 text-[10px]">{src.content.slice(0, 80)}...</p>
          </div>
        ))}
      </div>
    </div>
  );
}
