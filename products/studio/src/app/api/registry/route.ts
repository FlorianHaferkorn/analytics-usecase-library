import { NextResponse } from "next/server";
import path from "path";
import fs from "fs/promises";

function repoRoot(): string {
  if (process.env.REPO_ROOT) return process.env.REPO_ROOT;
  // products/studio/ → repo root is ../../
  return path.resolve(process.cwd(), "../../");
}

export async function GET() {
  try {
    const registryPath = path.join(repoRoot(), "tooling/ontology/out/master_registry.json");
    const raw = await fs.readFile(registryPath, "utf-8");
    const registry = JSON.parse(raw);
    return NextResponse.json(registry, {
      headers: { "Cache-Control": "s-maxage=60, stale-while-revalidate" },
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Unknown error";
    return NextResponse.json(
      { error: `Registry not found: ${msg}. Run: python tooling/ontology/registry_builder.py` },
      { status: 503 }
    );
  }
}
