# Native Fabric item generation

Status: implemented for explicit definition transport. Live deployment and semantic validation are separate, unfinished capabilities.

The Studio generation runner can package supplied Notebook, DataPipeline, SemanticModel and Report definitions alongside architecture documents and workspace creation requests. It preserves the author's native definitions; it does not invent notebook transformations, model measures, report visuals or connection identities.

## One source of truth

Add `physical_items` to the optional `architecture_input` module in the Project Package. The authoritative schema remains `tooling/generator/schemas/project_architecture_input.schema.json`.

Each item declares:

| Field | Purpose |
|---|---|
| `id`, `name`, `type` | Stable logical identity and exact target item name/type. |
| `workspace_ref`, `environment` | Owning declared physical workspace and the same environment. |
| `decision_refs` | Approved decision instances authorizing this design. |
| `depends_on` | Explicit logical item dependencies; cycles, unresolved references and cross-environment dependencies are rejected. |
| `definition` | Native `parts` containing `path`, `payload` and `payloadType: InlineBase64`, with a format where applicable. |
| `environment_bindings` | Explicit local assertions against a JSON part, with `part_path`, `json_pointer`, typed `expected_value` and `authority_ref`. An empty array declares no assertions. |
| `description` | Optional native item description. |

The same declarations appear as items in the architecture graph. Ownership and dependency edges come directly from these references. Graph details list definition part names without embedding Base64 payloads.

## Supported definition envelopes

| Item | Supported transport | Local checks | Still required |
|---|---|---|---|
| Notebook | FabricGitSource or ipynb | Exactly one notebook content part, optional platform metadata, format-compatible file extension. | Code review, dependencies, Spark settings, data bindings and execution tests. |
| DataPipeline | Native definition parts | `pipeline-content.json`, a properties object, JSON syntax and optional platform metadata. | Activity-specific schema validation, source/target permissions, connection binding and run evidence. |
| SemanticModel | TMDL or TMSL | `definition.pbism` and one format family; JSON syntax for JSON parts. | Full model validation, relationships, DAX correctness, identity path, refresh and query evidence. |
| Report | PBIR or PBIR-Legacy | `definition.pbir` and one report format family; JSON syntax for JSON parts. | Full visual schema validation, target model binding and rendered report checks. |

Base64 integrity, normalized relative part paths, duplicate names/IDs and metadata conflicts are checked for every item. A transport-ready result is not evidence that the content is semantically correct or accepted by a tenant.

JSON binding assertions address an exact value, for example `/properties/parameters/environment/defaultValue`, not a text occurrence somewhere in the document. They do not rewrite values. Assertions against source code or TMDL fail until an appropriate parser is available. The output explicitly retains `tenant_bindings_verified: false`.

## Generation workflow

1. Author and validate the Project Package, including physical workspace declarations and approved decision references.
2. Review and explicitly release the pinned input revision through the existing input-release workflow.
3. In Studio Automation, select `fabric_item_requests`, optionally together with `architecture_bundle` and `fabric_workspace_requests`.
4. Confirm local generation. All selected targets must pass preflight. A blocked target prevents the entire selected run from being recorded as successful.
5. Download the generated files and inspect the dependency plan, native request bodies and hash manifests.

Studio downloads a real ZIP containing the original artifact paths and `run-report.json`; no manual extraction from a JSON envelope is needed. ZIP timestamps are fixed for reproducible packaging. After reopening the page, a viewer can retrieve the same stored run without regenerating files or granting approval. The server checks project/revision identity and stored artifact hashes before returning it.

The Python seam is `tooling.superversion.project_package.automation`. Use an explicit revision with `--run --confirm-generation --actor <authenticated-actor> --target fabric_item_requests`. Studio obtains the actor from its server-side session; it must not trust a client-supplied identity.

The standalone `tooling.superversion.project_package.item_compile` module accepts `--repository`, `--schemas`, `--project-ref` and `--revision`. It consumes an existing release attestation and returns structured JSON; it cannot create an approval or call a tenant.

## Outputs and reproducibility

The item target contains:

- `fabric/item-plan.json`: ordered logical items, workspace references, local binding assertions, explicit limitations and source references.
- `fabric/items/<logical-id>.request.json`: the exact native Create Item body.
- `output-manifest.json`: project, revision, compiler-input hash, release-record hash and file hashes.

The path template `/v1/workspaces/{workspaceId}/items` is intentionally unresolved. A future executor must use a verified workspace-ID map; guessing IDs or replacing references by name alone is not supported. Dependencies determine order but do not remap embedded physical IDs inside native definitions.

Generation runs are stored outside immutable revision repositories under the sibling `automation-runs/<repository-name>/<revision>/<run-id>.json`. The run identity binds the compiler version, project revision, release record, selected targets, actor and file hashes. Timestamps are retained separately from this deterministic identity. Repeating the same request returns the existing record. Atomic writes and the project lock prevent partial publication; changing HEAD during generation blocks publication. Stored reports and artifacts are checked before reuse.

This sidecar is an execution record, not a new decision authority. It reports `scope: selected_generation_only`, `delivery_complete: false`, `apply_ready: false` and `tenant_actions_performed: false`.

## Verification and recovery

Focused local tests cover actual temporary repositories, input release, all three generation targets, concurrent retries, stale revisions, storage collisions, corrupted outputs, malformed definitions, dependency cycles and exact JSON-pointer checks. Run:

```powershell
py -3 -m pytest tooling/tests/test_project_item_compile.py tooling/tests/test_project_automation.py tooling/tests/test_project_architecture_compile.py -q
```

No tenant rollback is needed because this runner does not mutate a tenant. If inputs change, commit and review a new package revision and obtain its release before generating again. A corrupt sidecar is rejected; do not overwrite it to conceal the mismatch. Diagnose the file-integrity issue and retain evidence before deciding how to recover local storage.

## API grounding

Native API documentation checked on 2026-09-07:

- [Create Item](https://learn.microsoft.com/en-us/rest/api/fabric/core/items/create-item)
- [Notebook definition](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/notebook-definition)
- [DataPipeline definition](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/datapipeline-definition)
- [SemanticModel definition](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/semantic-model-definition)
- [Report definition](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/report-definition)

These references establish the definition envelope and supported formats. They do not prove this project's tenant permissions, item compatibility, runtime behavior or customer acceptance. Recheck capability support when adding an executor or another item type.
