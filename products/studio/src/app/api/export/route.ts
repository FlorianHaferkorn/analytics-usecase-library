import { NextRequest, NextResponse } from "next/server";
import path from "path";
import fs from "fs/promises";

function repoRoot(): string {
  if (process.env.REPO_ROOT) return process.env.REPO_ROOT;
  return path.resolve(process.cwd(), "../../");
}

export async function POST(req: NextRequest) {
  try {
    const { yamlText, exportPath } = await req.json();
    if (!yamlText || !exportPath) {
      return NextResponse.json({ error: "yamlText and exportPath are required" }, { status: 400 });
    }

    // Security: only allow writing inside core/usecases/
    const normalized = path.normalize(exportPath);
    if (!normalized.startsWith("core/usecases/") && !normalized.startsWith("core\\usecases\\")) {
      return NextResponse.json({ error: "Export path must be inside core/usecases/" }, { status: 403 });
    }

    const fullPath = path.join(repoRoot(), normalized);
    await fs.mkdir(path.dirname(fullPath), { recursive: true });
    await fs.writeFile(fullPath, yamlText, "utf-8");

    return NextResponse.json({ success: true, path: normalized });
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Unknown error";
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}
