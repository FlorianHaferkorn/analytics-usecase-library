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
    'Export a use case bracket to TMDL/Power BI format',
    { useCaseId: z.string().describe('Use case ID to export') },
    async ({ useCaseId }) => {
      const result = await tools.exportFabric(useCaseId);
      return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
    }
  );

  server.tool(
    'export_oss',
    'Export a use case bracket to SQL/Evidence.dev format',
    { useCaseId: z.string().describe('Use case ID to export') },
    async ({ useCaseId }) => {
      const result = await tools.exportOss(useCaseId);
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
