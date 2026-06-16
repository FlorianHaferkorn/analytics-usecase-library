# Studio as Activation Control Panel — UX concept

> **Decision record:** [`../architecture/adr/0003-customer-activation-and-capability-gating.md`](../architecture/adr/0003-customer-activation-and-capability-gating.md)
> · **Manifest spec:** [`capability-manifest.md`](capability-manifest.md)
>
> **Status:** UX concept. The goal: a non-technical customer activates and limits
> agent capabilities **without touching YAML or typing a slash command**. The
> Studio is the human face of the capability manifest.

## Core loop

```
[ UI toggles ] ──► writes aluca.capabilities.yaml ──► runs the generator ──► repo configs + MCP updated ──► doctor badge
```

The customer sees plain-language switches and a status badge. They never see the
manifest, the generated agent configs, or a slash command. (Engineers still can —
the Studio is a convenience over the manifest, not a replacement for it.)

## Screens (sketch)

1. **Capabilities** — plain-language toggles, each mapping 1:1 to a manifest
   field:
   - *Target tool* (Power BI / Metabase / Superset / Grafana) → `target`
   - *Use official Microsoft authoring (requires Node)* → `tiers.tier1_oracle`
   - *Live Desktop verification* → `tiers.tier2_desktop`
   - *Allow external tools / network* → `external.allow_external` / `allow_network`
     (default off, shown with an explicit security note and a confirm step)

2. **Skills** — a checklist of official + overlay skills with plain descriptions.
   ALUCA governance overlays are shown as **"always on / recommended"**; official
   mechanics skills are opt-in checkboxes.

3. **Status (doctor)** — a single badge answering *"is this safe right now?"*:
   active tier, what is external/off, the pinned upstream version. Mirrors
   `aluca doctor`.

4. **Apply** — one button: writes the manifest, regenerates configs, and shows a
   **diff** ("these repo files changed") for an admin to commit — or auto-commits
   in managed mode.

## Principles

- **Nothing silent.** The doctor badge always reflects real state; no capability
  turns on without showing up there.
- **Default-off external.** Enabling external/network requires an explicit
  confirm with a security note — never a quiet default.
- **Reversible.** Toggle off → regenerate → the capability is gone from every
  agent config at once.
- **Manifest stays the source of truth.** The Studio writes the **manifest** and
  runs the **generator**; it never writes agent configs directly. This keeps one
  audit surface and one deterministic path.
- **Slash commands absent from this surface.** They remain available to engineers
  but are not part of the customer flow.

The result: activation is **legible to non-technical users** and **auditable for
security** — through the same single artifact.
