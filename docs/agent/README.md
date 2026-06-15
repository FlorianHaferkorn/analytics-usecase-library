# Agent Rules and Skills (Canonical Location)

This directory is the **single source of truth (SSOT)** for all agent rules and skills used in ALUCA (Analytics Library of Use Cases). Tool-specific configurations (`.cursor/`, `.github/`, etc.) are **generated** from these canonical files.

## Structure

```
docs/agent/
  rules/          # One .md file per rule (pure Markdown, no tool-specific frontmatter)
    _index.yaml   # Metadata for all rules (description, alwaysApply, globs)
    *.md          # Rule content
  skills/         # One .md file per skill (pure Markdown, no tool-specific frontmatter)
    _index.yaml   # Metadata for all skills (name, description)
    *.md          # Skill content
```

## Design Principles

- **Rules and skills are pure Markdown.** They contain no tool-specific frontmatter (no Cursor `---` blocks, no GitHub Actions YAML, etc.). This makes them readable by any AI tool or human.
- **Metadata lives in `_index.yaml` files.** Each subdirectory has an `_index.yaml` that stores metadata extracted from tool-specific configs (description, globs, alwaysApply for rules; name and description for skills).
- **A generator script produces tool-specific wrappers.** The generator reads the canonical `.md` files and `_index.yaml` metadata, then outputs tool-specific configs with the appropriate frontmatter and structure.
- **Generated files have AUTO-GENERATED headers.** Any file produced by the generator includes a comment or frontmatter marker indicating it was auto-generated and should not be edited directly.

## Currently Generated Targets

| Target | Output Location | Format |
|--------|----------------|--------|
| Cursor rules | `.cursor/rules/*.mdc` | MDC with YAML frontmatter (`description`, `alwaysApply`, `globs`) |
| Cursor skills | `.cursor/skills/*/SKILL.md` | Markdown with YAML frontmatter (`name`, `description`) |

Future targets may include `.github/`, Copilot instructions, or other tool-specific formats.

## Workflow

1. **Edit rules and skills here** in `docs/agent/`.
2. **Update `_index.yaml`** if metadata changes (new rule, changed globs, etc.).
3. **Run the generator** to produce tool-specific configs.
4. **Commit both** the canonical source and the generated output.

Do not edit generated files (`.cursor/rules/*.mdc`, `.cursor/skills/*/SKILL.md`) directly. Changes will be overwritten on the next generator run.
