# Organization (Org-Registry)

This folder holds the **framework** org role registry: schema reference and a **minimal** role list.

## Contents

- **Schema:** The authoritative schema for org role files is `tooling/validation/schemas/org_roles.schema.json`. All `org_roles.yaml` files must conform to it.
- **Minimal `org_roles.yaml`:** The file in this folder contains only the role IDs referenced by `core/usecases/` and `core/action_codes/` (id, title, domain). This keeps the framework self-consistent so Stage 1 and the registry can run without a customer showcase.

## Customer / showcase-specific lists

Full or customer-specific role lists (with titles, aliases, etc.) live under showcases, for example:

- `showcases/aurora_group/organization/org_roles.yaml`

## Path resolution (tooling)

Registry builder and schema validation resolve the org roles file as follows:

1. **Primary (override):** If `showcases/aurora_group/organization/org_roles.yaml` exists, it is used for role validation and schema validation of that file.
2. **Fallback:** Otherwise `core/organization/org_roles.yaml` is used.

So in this repo, with the Aurora showcase present, validation runs against the full Aurora list. Without the showcase (or in other repos), the minimal list in core is used.

Maintenance scripts (e.g. `migrate_action_code_roles_to_ids.py`, `migrate_brackets_v2.py`) use the **core** path only, for framework-context migrations.
