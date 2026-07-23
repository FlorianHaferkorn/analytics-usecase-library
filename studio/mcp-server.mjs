#!/usr/bin/env node

/**
 * ALUCA Studio MCP Server — Entry Point
 *
 * Usage:
 *   npx tsx mcp-server.mjs
 *   # or add to package.json scripts: "mcp": "tsx mcp-server.mjs"
 *
 * Add to your MCP client config:
 *   {
 *     "mcpServers": {
 *       "aluca-studio": {
 *         "command": "npx",
 *         "args": ["tsx", "studio/mcp-server.mjs"],
 *         "cwd": "/path/to/analytics-usecase-library"
 *       }
 *     }
 *   }
 */

import { startServer } from './src/lib/mcp/server.ts';

startServer().catch((err) => {
  console.error('MCP server failed to start:', err);
  process.exit(1);
});
