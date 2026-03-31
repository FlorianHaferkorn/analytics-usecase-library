# fabric-item-definitions.md — Fabric Item Definition Structures

> **Source**: `microsoft/skills-for-fabric` ITEM-DEFINITIONS-CORE.md
> **Purpose**: Definition envelope, platform file, per-item-type parts, content structure, and decoded examples.
> Used by skills that create, read, or update item definitions programmatically.

---

## Definition Envelope

All definition payloads share a common envelope:

```json
{
  "definition": {
    "format": "<format>",
    "parts": [
      {
        "path": "<filePath>",
        "payload": "<base64-encoded-content>",
        "payloadType": "InlineBase64"
      }
    ]
  }
}
```

- `format` — item-type-specific (e.g. `ipynb`, `TMDL`, `PBIR`). Most item types have a single default format (omit or set to `null`).
- `parts` — array of definition files. Each part has a `path` (file name/path), `payload` (Base64-encoded content), and `payloadType` (always `InlineBase64`).

### Platform File

The `.platform` part contains item metadata (type, display name, description, logical ID). It is:
- **Returned** by Get Item Definition (always included).
- **Accepted** by Create Item with Definition (optional).
- **Accepted** by Update Item Definition **only** when `?updateMetadata=true` is set.

> **Gotcha**: Omitting `?updateMetadata=true` silently ignores the `.platform` part.

## Per-Item-Type Definitions

### Support Matrix

| Item Type | Supported Formats | Notes |
|---|---|---|
| Notebook | `ipynb`, `FabricGitSource` | |
| DataPipeline | *(default)* | |
| SemanticModel | `TMSL`, `TMDL` (Prefer TMDL) | |
| Report | `PBIR-Legacy`, `PBIR` (Prefer PBIR) | |
| Lakehouse | `LakehouseDefinitionV1` | |
| SparkJobDefinition | `SparkJobDefinitionV1`, `SparkJobDefinitionV2` | |
| Environment | *(default, set format to null)* | |
| Eventhouse | `JSON` | |
| KQLDatabase | `JSON` | |
| VariableLibrary | *(default — do NOT include format field)* | Critical gotcha |

> Full schema index: https://github.com/microsoft/json-schemas/tree/main/fabric/item

---

### SemanticModel

> Spec: https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/semantic-model-definition

**Formats**: `TMSL`, `TMDL` (prefer TMDL — text-based, diff-friendly)

**TMDL Parts:**

| Part Path | Content | Required |
|---|---|---|
| `definition/database.tmdl` | Database definition | Yes |
| `definition/model.tmdl` | Model definition | Yes |
| `definition/tables/<TableName>.tmdl` | Per-table definitions | Yes (≥1) |
| `definition.pbism` | Semantic model connection | Yes |
| `diagramLayout.json` | Diagram layout | No |
| `.platform` | Item metadata JSON | No |

**TMSL Parts:**

| Part Path | Content | Required |
|---|---|---|
| `model.bim` | Tabular model JSON (TMSL) | Yes |
| `definition.pbism` | Semantic model connection | Yes |
| `diagramLayout.json` | Diagram layout | No |
| `.platform` | Item metadata JSON | No |

> **Critical**: The API replaces entire definitions during updates — all parts (modified and unmodified) must be included, or omitted parts are deleted. Never include `.platform` in update payloads unless using `?updateMetadata=true`.

---

### Report

> Spec: https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/report-definition
> JSON Schemas: [`report/3.1.0`](https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.1.0/schema.json)

**Formats**: `PBIR-Legacy`, `PBIR` (prefer PBIR — per-visual files, diff-friendly)

**PBIR Parts:**

| Part Path | Content | Required |
|---|---|---|
| `definition/report.json` | Report-level settings | Yes |
| `definition/version.json` | Format version | Yes |
| `definition/pages/pages.json` | Page listing | Yes |
| `definition/pages/<pageId>/page.json` | Per-page layout | Yes |
| `definition/pages/<pageId>/visuals/<visualId>/visual.json` | Per-visual config | Yes |
| `definition.pbir` | Semantic model reference | Yes |
| `StaticResources/RegisteredResources/*` | Custom visuals, images, themes | No |
| `.platform` | Item metadata JSON | No |

**PBIR-Legacy Parts:**

| Part Path | Content | Required |
|---|---|---|
| `report.json` | Report layout and visuals | Yes |
| `definition.pbir` | Semantic model reference | Yes |
| `StaticResources/RegisteredResources/*` | Custom visuals, images, themes | No |
| `.platform` | Item metadata JSON | No |

> **Important**: `definition.pbir` holds the semantic model reference. Fabric REST API only supports `byConnection` references (not `byPath`).

---

### Notebook

> Spec: https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/notebook-definition

**Formats**: `ipynb` (default), `FabricGitSource`

| Part Path | Content | Required |
|---|---|---|
| `notebook-content.ipynb` (ipynb format) | Jupyter notebook JSON | Yes |
| `notebook-content.py` / `.sql` / `.scala` / `.r` (FabricGitSource) | Source code with metadata comments | Yes |
| `.platform` | Item metadata JSON | No |

**Decoded ipynb content** (standard Jupyter format):

```json
{
  "nbformat": 4,
  "nbformat_minor": 5,
  "cells": [
    {
      "cell_type": "code",
      "source": ["# Welcome to your new notebook\n"],
      "execution_count": null,
      "outputs": [],
      "metadata": {}
    }
  ],
  "metadata": {
    "language_info": { "name": "python" }
  }
}
```

> **Gotcha**: `execution_count` must be `null` and `outputs` must be `[]` — non-empty values cause import failures.

---

### DataPipeline

> Spec: https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/datapipeline-definition

**Formats**: *(default — no format parameter needed)*

| Part Path | Content | Required |
|---|---|---|
| `pipeline-content.json` | Pipeline activities JSON | Yes |
| `.platform` | Item metadata JSON | No |

**Decoded content structure**:

```json
{
  "properties": {
    "description": "Pipeline description",
    "activities": [
      {
        "name": "ActivityName",
        "type": "TridentNotebook",
        "dependsOn": [],
        "policy": {
          "timeout": "0.12:00:00",
          "retry": 0,
          "retryIntervalInSeconds": 30
        },
        "typeProperties": {
          "notebookId": "<guid>",
          "workspaceId": "<guid>"
        }
      }
    ]
  }
}
```

**Key activity types**: `TridentNotebook`, `Copy`, `Lookup`, `GetMetadata`, `ForEach`, `IfCondition`, `Switch`, `Until`, `Wait`, `Fail`, `SetVariable`, `AppendVariable`, `ExecutePipeline`, `SparkJobDefinition`, `Script`, `WebActivity`, `PBISemanticModelRefresh`, `Delete`, `Filter`.

---

### Lakehouse

> Spec: https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/lakehouse-definition

**Format**: `LakehouseDefinitionV1`

| Part Path | Content | Required |
|---|---|---|
| `lakehouse.metadata.json` | Lakehouse properties | Yes |
| `shortcuts.metadata.json` | OneLake shortcuts array | No |
| `data-access-roles.json` | Data access roles | No |
| `.platform` | Item metadata JSON | No |

**Decoded lakehouse.metadata.json**:
```json
{ "defaultSchema": "dbo" }
```

**Decoded shortcuts.metadata.json** (supported target types: `OneLake`, `AdlsGen2`, `AmazonS3`, `GoogleCloudStorage`, `S3Compatible`, `Dataverse`):

```json
[
  {
    "name": "TestShortcut",
    "path": "/Tables/dbo",
    "target": {
      "type": "OneLake",
      "oneLake": {
        "path": "Tables/dbo/publicholidays",
        "itemId": "00000000-0000-0000-0000-000000000000",
        "workspaceId": "00000000-0000-0000-0000-000000000000"
      }
    }
  }
]
```

---

### SparkJobDefinition

> Spec: https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/spark-job-definition

**Formats**: `SparkJobDefinitionV1`, `SparkJobDefinitionV2`

> **Note**: V2 only supports `.py` and `.R` files. JAR files are not supported. The JSON file is named `SparkJobDefinitionV1.json` even in V2 format (historical naming).

| Part Path (V2) | Content | Required |
|---|---|---|
| `SparkJobDefinitionV1.json` | Job configuration JSON | Yes |
| `Main/<filename>` | Main executable (.py or .R) | No |
| `Libs/<filename>` | Library files — multiple allowed | No |
| `.platform` | Item metadata JSON | No |

**Decoded SparkJobDefinitionV1.json**:

```json
{
  "executableFile": null,
  "defaultLakehouseArtifactId": "",
  "mainClass": "",
  "additionalLakehouseIds": [],
  "retryPolicy": null,
  "commandLineArguments": "",
  "additionalLibraryUris": [],
  "language": "",
  "environmentArtifactId": null
}
```

---

### VariableLibrary

> Spec: https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/variable-library-definition

> **CRITICAL**: Variable Library does **NOT** support the `format` field. Omit it entirely — including `"format": null` may cause errors.

| Part Path | Content | Required |
|---|---|---|
| `variables.json` | Variable names, types, and default values | Yes |
| `settings.json` | Value Set ordering and library settings | Yes |
| `valueSets/<name>.json` | Per-environment overrides | Only when using Value Sets |
| `.platform` | Item metadata JSON | No |

**Supported Variable Types**: `String`, `Boolean`, `Number`, `Integer`, `DateTime`, `ItemReference`

**variables.json:**

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/variableLibrary/definition/variables/1.0.0/schema.json",
  "variables": [
    { "name": "lakehouse_name", "note": "", "type": "String", "value": "bronze_lakehouse" },
    { "name": "enable_logging", "note": "", "type": "Boolean", "value": "true" },
    {
      "name": "target_warehouse",
      "note": "",
      "type": "ItemReference",
      "value": {
        "itemId": "bbbbbbbb-1111-2222-3333-cccccccccccc",
        "workspaceId": "aaaaaaaa-0000-1111-2222-bbbbbbbbbbbb"
      }
    }
  ]
}
```

**Pipeline type mappings** (do NOT use Variable Library type names directly):

| Variable Library Type | Pipeline Type |
|---|---|
| Boolean | **Bool** |
| Integer | **Int** |
| Number | **Double** |
| DateTime | **String** |
| String | **String** |
| ItemReference | **String** |

**VariableLibrary Gotchas:**

| Issue | Resolution |
|---|---|
| `.get("lib", "var")` fails at runtime | Use `getLibrary("lib").var` — always dot notation |
| `bool("false")` → `True` in Python | Compare as string: `.lower() == "true"` |
| Definition rejected — format field | Omit `format` entirely — not supported |
| Pipeline variable wrong type | Map correctly: Boolean→Bool, Integer→Int, Number→Double |
| Pipeline expression literal | Wrap in `{"value": "...", "type": "Expression"}` |
| Value Sets ignored | Add `valueSetsOrder` to `settings.json` |

---

### Eventhouse

**Format**: `JSON`

| Part Path | Content | Required |
|---|---|---|
| `EventhouseProperties.json` | Eventhouse properties (currently `{}`) | Yes |
| `.platform` | Item metadata JSON | No |

---

### KQLDatabase

**Format**: `JSON`

| Part Path | Content | Required |
|---|---|---|
| `DatabaseProperties.json` | Database configuration JSON | Yes |
| `DatabaseSchema.kql` | KQL schema script | No |
| `.platform` | Item metadata JSON | No |

**Decoded DatabaseProperties.json**:

```json
{
  "databaseType": "ReadWrite",
  "parentEventhouseItemId": "<eventhouse-item-id>",
  "oneLakeCachingPeriod": "P36500D",
  "oneLakeStandardStoragePeriod": "P365000D"
}
```
