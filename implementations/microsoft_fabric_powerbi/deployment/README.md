# Deployment (setup / teardown by code)

Goal: make the Fabric/Power BI implementation **easy to create and delete** (idempotent, parameterized, environment-aware).

## What we will put here

- Environment definitions: dev/test/prod (naming, regions, capacity)
- Workspace provisioning (Data Engineering, Data Models, Reporting, Shared)
- Optional: Lakehouse + Dataflows Gen2 provisioning
- Git integration / PBIP repo connection strategy
- Deployment pipelines strategy (or CI/CD workflow) for promoting artifacts
- Teardown scripts with safety rails (never delete the wrong tenant/workspaces)

## Recommended interfaces (to decide)

One of:
- PowerShell + Fabric REST APIs
- Terraform (if provider support is sufficient)
- Bicep/ARM (where applicable)

We’ll keep V1 minimal and deterministic; V2 can expand.

