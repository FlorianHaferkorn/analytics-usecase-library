#!/usr/bin/env tsx
// ============================================================================
// validate-grid.ts — build-time & CI grid validator
// ----------------------------------------------------------------------------
// Scans the src/ tree for <Slot ... /> usages and validates:
//   - col + cs <= 12, row + rs <= 12
//   - No two slots on the same logical page overlap
//
// Slots are grouped by the file they appear in (one file = one page template).
// Exits with code 1 on any violation.
// ============================================================================

import { readFileSync } from "node:fs";
import { glob } from "node:fs/promises";
import { resolve } from "node:path";
import {
  validateSlot,
  slotsOverlap,
  type SlotCoords,
} from "../src/grid/slot-pos.js";

interface FoundSlot extends SlotCoords {
  slotId: string;
  file: string;
  lineNumber: number;
}

const SLOT_RE =
  /<Slot\s+([^/>]*?)\/?>/gs; /* matches <Slot ... /> (self-closing) */

function parseAttr(attrs: string, name: string): number | string | null {
  // matches: name={123}, name={1.5}, name="str", name={"str"}, name={-1}
  const reNum = new RegExp(`\\b${name}\\s*=\\s*\\{\\s*(-?\\d+(?:\\.\\d+)?)\\s*\\}`);
  const mNum = attrs.match(reNum);
  if (mNum?.[1]) return Number(mNum[1]);

  const reStr = new RegExp(
    `\\b${name}\\s*=\\s*(?:"([^"]*)"|'([^']*)'|\\{\\s*["']([^"']*)["']\\s*\\})`,
  );
  const mStr = attrs.match(reStr);
  if (mStr) return mStr[1] ?? mStr[2] ?? mStr[3] ?? null;

  return null;
}

function scanFile(file: string): FoundSlot[] {
  const text = readFileSync(file, "utf-8");
  const found: FoundSlot[] = [];

  let m: RegExpExecArray | null;
  while ((m = SLOT_RE.exec(text)) !== null) {
    const attrs = m[1] ?? "";
    const col = parseAttr(attrs, "col");
    const row = parseAttr(attrs, "row");
    const cs = parseAttr(attrs, "cs");
    const rs = parseAttr(attrs, "rs");
    const slotId = parseAttr(attrs, "slotId");

    if (
      typeof col !== "number" ||
      typeof row !== "number" ||
      typeof cs !== "number" ||
      typeof rs !== "number"
    ) {
      // Slot uses non-literal values (e.g. variables) — skip static validation
      continue;
    }

    const upToMatch = text.slice(0, m.index);
    const lineNumber = upToMatch.split("\n").length;

    found.push({
      col,
      row,
      cs,
      rs,
      slotId: typeof slotId === "string" ? slotId : "(unknown)",
      file,
      lineNumber,
    });
  }

  return found;
}

async function main(): Promise<void> {
  const root = resolve(import.meta.dirname ?? ".", "..");
  const pattern = "src/**/*.tsx";
  const files: string[] = [];

  // Use Node's native fs.promises.glob (Node 22+) OR fall back.
  try {
    for await (const f of glob(pattern, { cwd: root })) {
      files.push(resolve(root, f));
    }
  } catch {
    // Older Node: use a simple manual walk (kept minimal).
    const { readdirSync, statSync } = await import("node:fs");
    const walk = (dir: string): void => {
      for (const entry of readdirSync(dir)) {
        const p = resolve(dir, entry);
        if (statSync(p).isDirectory()) walk(p);
        else if (p.endsWith(".tsx")) files.push(p);
      }
    };
    walk(resolve(root, "src"));
  }

  const slotsByFile = new Map<string, FoundSlot[]>();
  let totalSlots = 0;
  const overflowErrors: string[] = [];
  const overlapErrors: string[] = [];

  for (const f of files) {
    const slots = scanFile(f);
    if (slots.length === 0) continue;
    slotsByFile.set(f, slots);
    totalSlots += slots.length;

    for (const s of slots) {
      const errs = validateSlot(s);
      for (const e of errs) {
        overflowErrors.push(
          `  ${f}:${s.lineNumber}  slotId="${s.slotId}"  ${e.message}`,
        );
      }
    }

    // Pairwise overlap check within same file
    for (let i = 0; i < slots.length; i++) {
      for (let j = i + 1; j < slots.length; j++) {
        const a = slots[i]!;
        const b = slots[j]!;
        if (slotsOverlap(a, b)) {
          overlapErrors.push(
            `  ${f}  slot "${a.slotId}" (line ${a.lineNumber}) overlaps "${b.slotId}" (line ${b.lineNumber})`,
          );
        }
      }
    }
  }

  console.log(
    `[grid-validator] scanned ${files.length} file(s), found ${totalSlots} slot(s) across ${slotsByFile.size} page(s)`,
  );

  if (overflowErrors.length > 0) {
    console.error("\n[grid-validator] OVERFLOW ERRORS:");
    overflowErrors.forEach((e) => console.error(e));
  }
  if (overlapErrors.length > 0) {
    console.error("\n[grid-validator] OVERLAP ERRORS:");
    overlapErrors.forEach((e) => console.error(e));
  }

  if (overflowErrors.length + overlapErrors.length > 0) {
    console.error(
      `\n[grid-validator] FAILED: ${overflowErrors.length} overflow(s), ${overlapErrors.length} overlap(s)`,
    );
    process.exit(1);
  }

  console.log("[grid-validator] OK — all slots valid, no overlaps");
}

main().catch((err) => {
  console.error("[grid-validator] unexpected error:", err);
  process.exit(2);
});
