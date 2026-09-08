/**
 * MCP Server — Exposes Studio's Core loaders and adapters as MCP tools.
 *
 * Run with: node mcp-server.mjs
 * Connect via stdio transport.
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';
import * as tools from './tools';

export function createMcpServer(): McpServer {
  const server = new McpServer({
    name: 'actionready-studio',
    version: '0.1.0',
  });

  // --- Tools ---

  server.tool('list_kpis', 'List all KPIs from the catalog', {}, async () => {
    const kpis = await tools.listKpis();
    return { content: [{ type: 'text', text: JSON.stringify(kpis, null, 2) }] };
  });

  server.tool('list_brackets', 'List all use case brackets', {}, async () => {
    const brackets = await tools.listBrackets();
    return { content: [{ type: 'text', text: JSON.stringify(brackets, null, 2) }] };
  });

  server.tool('list_actions', 'List all action codes', {}, async () => {
    const actions = await tools.listActions();
    return { content: [{ type: 'text', text: JSON.stringify(actions, null, 2) }] };
  });

  server.tool(
    'get_bracket',
    'Get a specific use case bracket by ID',
    { id: z.string().describe('Use case bracket ID (e.g. COM-001)') },
    async ({ id }) => {
      const result = await tools.getBracket(id);
      return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
    }
  );

  server.tool(
    'validate_yaml',
    'Validate YAML content against a JSON schema',
    {
      yaml: z.string().describe('YAML content to validate'),
      schema: z.string().describe('Schema name (e.g. usecase_bracket, kpi_definition)'),
    },
    async ({ yaml, schema }) => {
      const result = await tools.validateYaml(yaml, schema);
      return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
    }
  );

  server.tool(
    'export_fabric',
    'Package a use case as governed TMDL and PBIR artifacts with the shared gate report',
    { useCaseId: z.string().describe('Use case ID to export') },
    async ({ useCaseId }) => {
      const result = await tools.exportFabric(useCaseId);
      return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
    }
  );

  server.tool(
    'export_oss',
    'Package a use case as a governed Open Semantic Interchange artifact',
    { useCaseId: z.string().describe('Use case ID to export') },
    async ({ useCaseId }) => {
      const result = await tools.exportOss(useCaseId);
      return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
    }
  );

  // ── Write tools ──────────────────────────────────────────────────────────

  server.tool(
    'create_bracket',
    'Save a use case bracket YAML draft to the Studio database',
    {
      bracketId: z.string().describe('Bracket ID (e.g. COM-001)'),
      yamlContent: z.string().describe('Full UseCase_Bracket YAML content'),
      projectId: z.string().optional().describe('Project ID (default: "default")'),
    },
    async ({ bracketId, yamlContent, projectId }) => {
      const result = await tools.createBracket(bracketId, yamlContent, projectId);
      return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
    }
  );

  server.tool(
    'publish_draft',
    'Submit a bracket draft for governance review',
    {
      bracketId: z.string().describe('Bracket ID to submit for review'),
      actorEmail: z.string().describe('Email of the submitter'),
      justification: z.string().optional().describe('Justification for the submission'),
      projectId: z.string().optional().describe('Project ID (default: "default")'),
    },
    async ({ bracketId, actorEmail, justification, projectId }) => {
      const result = await tools.publishDraft(bracketId, actorEmail, justification, projectId);
      return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
    }
  );

  server.tool(
    'run_generator',
    'Run the export generator for a use case (fabric or oss)',
    {
      useCaseId: z.string().describe('Use case ID to generate output for'),
      connector: z.enum(['fabric', 'oss']).describe('Target connector: fabric or oss'),
    },
    async ({ useCaseId, connector }) => {
      const result = await tools.runGenerator(useCaseId, connector);
      return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
    }
  );

  server.tool(
    'validate_bindings',
    'Run validate_bindings.py and return the output',
    {
      strict: z.boolean().optional().describe('Enable --strict mode'),
    },
    ({ strict }) => {
      const result = tools.validateBindings(strict ?? false);
      return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
    }
  );

  server.tool(
    'execute_dax',
    'Execute a DAX query against a Fabric semantic model via execute_dax.py (requires fab + az CLI)',
    {
      workspaceId: z.string().describe('Fabric workspace ID or friendly name'),
      datasetId: z.string().describe('Semantic model ID or friendly name'),
      daxQuery: z.string().describe('DAX query to execute (e.g. EVALUATE ROW("Value", [My Measure]))'),
      outputFormat: z.enum(['json', 'csv', 'table']).optional().describe('Output format (default: json)'),
    },
    ({ workspaceId, datasetId, daxQuery, outputFormat }) => {
      const result = tools.executeDax(workspaceId, datasetId, daxQuery, outputFormat ?? 'json');
      return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
    }
  );

  server.tool(
    'deploy_pbip',
    'Generate a governed PBIP package and import it with fab only when all target gates are live',
    {
      useCaseId: z.string().describe('Use case ID to generate and deploy (e.g. COM-001)'),
      workspaceName: z.string().describe('Fabric workspace friendly name'),
      distPath: z.string().optional().describe('Override dist output path'),
    },
    async ({ useCaseId, workspaceName, distPath }) => {
      const result = await tools.deployPbip(useCaseId, workspaceName, distPath);
      return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
    }
  );

  server.tool(
    'refresh_dataset',
    'Trigger a Full refresh of a Fabric semantic model via fab api',
    {
      workspaceId: z.string().describe('Fabric workspace GUID'),
      datasetId: z.string().describe('Semantic model / dataset GUID'),
    },
    ({ workspaceId, datasetId }) => {
      const result = tools.refreshDataset(workspaceId, datasetId);
      return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
    }
  );

  server.tool(
    'autofix_bindings',
    'Audit PBIR bindings without mutating generated files; defects must be fixed at their governed source',
    {
      distPath: z.string().optional().describe('Override path to PBIP dist folder'),
    },
    ({ distPath }) => {
      const result = tools.autofixBindings(distPath);
      return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
    }
  );

  server.tool(
    'create_kpi',
    'Create or update a KPI YAML definition in core/kpi_catalog/',
    {
      kpiId: z.string().describe('KPI ID (e.g. com.net_sales.amount)'),
      yamlContent: z.string().describe('Full KPI YAML content'),
    },
    ({ kpiId, yamlContent }) => {
      const result = tools.createKpi(kpiId, yamlContent);
      return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
    }
  );

  server.tool(
    'update_action',
    'Create or update an action code YAML in core/action_codes/',
    {
      actionId: z.string().describe('Action code ID (e.g. C-M2.1)'),
      yamlContent: z.string().describe('Full action code YAML content'),
    },
    ({ actionId, yamlContent }) => {
      const result = tools.updateAction(actionId, yamlContent);
      return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
    }
  );

  return server;
}

/** Start the MCP server with stdio transport. */
export async function startServer() {
  const server = createMcpServer();
  const transport = new StdioServerTransport();
  await server.connect(transport);
}
