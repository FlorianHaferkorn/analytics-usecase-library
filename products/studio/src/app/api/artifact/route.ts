import { NextRequest, NextResponse } from "next/server";
import path from "path";
import fs from "fs/promises";

function repoRoot(): string {
  if (process.env.REPO_ROOT) return process.env.REPO_ROOT;
  return path.resolve(process.cwd(), "../../");
}

/** GET /api/artifact?path=core/usecases/core/COM-001_.../UseCase_Bracket.yaml */
export async function GET(req: NextRequest) {
  const relPath = req.nextUrl.searchParams.get("path");
  if (!relPath) {
    return NextResponse.json({ error: "path param required" }, { status: 400 });
  }

  const normalized = path.normalize(relPath);
  // Security: only allow reading inside core/
  if (!normalized.startsWith("core/") && !normalized.startsWith("core\\")) {
    return NextResponse.json({ error: "Path must be inside core/" }, { status: 403 });
  }

  try {
    const fullPath = path.join(repoRoot(), normalized);
    const content = await fs.readFile(fullPath, "utf-8");
    return NextResponse.json({ content, path: normalized });
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Read failed";
    return NextResponse.json({ error: msg }, { status: 404 });
  }
}

/** POST /api/artifact — write YAML back to a core/ file */
export async function POST(req: NextRequest) {
  try {
    const { content, path: relPath } = await req.json();
    if (!content || !relPath) {
      return NextResponse.json({ error: "content and path required" }, { status: 400 });
    }

    const normalized = path.normalize(relPath);
    // Security: restrict writes to known safe directories
    const allowedPrefixes = ["core/usecases/", "core/kpi_catalog/", "core/action_codes/", "core/semantic_models/"];
    const isAllowed = allowedPrefixes.some(
      (p) => normalized.startsWith(p) || normalized.startsWith(p.replace(/\//g, "\\"))
    );
    if (!isAllowed) {
      return NextResponse.json(
        { error: `Write not allowed to: ${normalized}. Must be under core/usecases/, core/kpi_catalog/, or core/action_codes/` },
        { status: 403 }
      );
    }

    const fullPath = path.join(repoRoot(), normalized);
    await fs.mkdir(path.dirname(fullPath), { recursive: true });
    await fs.writeFile(fullPath, content, "utf-8");

    return NextResponse.json({ success: true, path: normalized });
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Write failed";
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}
