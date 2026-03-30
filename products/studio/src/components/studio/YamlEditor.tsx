"use client";
import { useState } from "react";
import { useStudio } from "@/store/studio";
import { validateDraft, exportPath } from "@/lib/bracket";
import { Button } from "@/components/ui/Button";

export function YamlEditor() {
  const {
    yamlText, setYamlText, syncDraftFromYaml, syncYamlFromDraft, draft,
  } = useStudio();

  const [parseError, setParseError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [exportMsg, setExportMsg] = useState<{ ok: boolean; text: string } | null>(null);

  function handleSync() {
    const err = syncDraftFromYaml();
    setParseError(err);
    if (!err) setExportMsg(null);
  }

  function handleReformat() {
    const err = syncDraftFromYaml();
    if (!err) {
      syncYamlFromDraft();
      setParseError(null);
    } else {
      setParseError(err);
    }
  }

  async function handleExport() {
    // First sync draft from YAML
    const err = syncDraftFromYaml();
    if (err) { setParseError(err); return; }

    const validation = validateDraft(draft);
    if (!validation.valid) {
      setExportMsg({ ok: false, text: validation.errors.join(" · ") });
      return;
    }

    setExporting(true);
    try {
      const path = exportPath(draft);
      const res = await fetch("/api/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ yamlText, exportPath: path }),
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setExportMsg({ ok: true, text: `Exported to ${path}` });
    } catch (e) {
      setExportMsg({ ok: false, text: e instanceof Error ? e.message : "Export failed" });
    } finally {
      setExporting(false);
    }
  }

  // Live validation
  const validation = (() => {
    try {
      return validateDraft(draft);
    } catch {
      return { valid: false, errors: [], warnings: [] };
    }
  })();

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="px-3 py-2 border-b border-slate-200 shrink-0 flex items-center gap-2 flex-wrap">
        <Button size="sm" variant="secondary" onClick={handleSync}>
          ↑ Apply YAML
        </Button>
        <Button size="sm" variant="ghost" onClick={handleReformat}>
          Reformat
        </Button>
        <Button size="sm" variant="secondary" onClick={syncYamlFromDraft}>
          ↓ Refresh from tree
        </Button>
        <Button size="sm" onClick={handleExport} loading={exporting} className="ml-auto">
          Export to repo
        </Button>
      </div>

      {/* Validation bar */}
      {(parseError || validation.errors.length > 0 || validation.warnings.length > 0) && (
        <div className="px-3 py-2 border-b border-slate-200 shrink-0 space-y-1">
          {parseError && (
            <p className="text-xs text-red-600">⛔ {parseError}</p>
          )}
          {validation.errors.map((e, i) => (
            <p key={i} className="text-xs text-red-600">⛔ {e}</p>
          ))}
          {validation.warnings.map((w, i) => (
            <p key={i} className="text-xs text-yellow-600">⚠ {w}</p>
          ))}
        </div>
      )}

      {/* Export message */}
      {exportMsg && (
        <div
          className={`px-3 py-1.5 text-xs border-b border-slate-200 shrink-0
            ${exportMsg.ok ? "bg-green-50 text-green-700" : "bg-red-50 text-red-600"}`}
        >
          {exportMsg.ok ? "✓" : "✕"} {exportMsg.text}
        </div>
      )}

      {/* YAML textarea */}
      <textarea
        value={yamlText}
        onChange={(e) => {
          setYamlText(e.target.value);
          setParseError(null);
          setExportMsg(null);
        }}
        className="flex-1 yaml-editor bg-slate-950 text-green-300 p-4 resize-none focus:outline-none w-full"
        spellCheck={false}
        autoComplete="off"
        autoCorrect="off"
      />
    </div>
  );
}
