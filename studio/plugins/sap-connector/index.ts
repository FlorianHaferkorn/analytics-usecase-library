/**
 * SAP Connector Studio Plugin
 *
 * Integrates the Python SAPConnectorAdapter with Studio's plugin hook system.
 * Hook handlers fire at each stage of the extract → land → promote pipeline
 * so Studio can display progress, log audit events, and surface errors.
 *
 * Hook lifecycle
 * --------------
 * onConnectorExtract  → fired before extraction starts; receives SAPConfig
 * onConnectorLand     → fired after each entity lands in the bronze zone
 * onConnectorPromote  → fired when bronze Parquet is ready for dbt promotion
 */

import type { Plugin, PluginContext } from '@/lib/plugins/types';

export interface SAPConnectorConfig {
  base_url: string;
  client: string;
  auth_type: 'basic' | 'oauth2';
  username?: string;
  password?: string;
  oauth_token?: string;
  page_size?: number;
  fiscal_year_filter?: number;
  entities?: string[];
}

export interface ConnectorExtractEvent {
  source_system: string;
  config: SAPConnectorConfig;
  entities: string[];
  triggered_by: string;
}

export interface ConnectorLandEvent {
  source_system: string;
  entity: string;
  records_extracted: number;
  files_written: string[];
  bronze_path: string;
}

export interface ConnectorPromoteEvent {
  source_system: string;
  entities: string[];
  bronze_root: string;
  silver_root: string;
  ready_for_dbt: boolean;
}

const sapConnectorPlugin: Plugin = {
  id: 'sap-connector',
  version: '1.0.0',

  hooks: {
    onConnectorExtract: async (
      event: ConnectorExtractEvent,
      ctx: PluginContext,
    ): Promise<void> => {
      ctx.logger.info(
        `[sap-connector] Starting extraction for entities: ${event.entities.join(', ')}`,
      );

      await ctx.audit.log({
        action: 'connector.extract.start',
        actor: event.triggered_by,
        resource: `connector:${event.source_system}`,
        metadata: {
          entities: event.entities,
          base_url: event.config.base_url,
          client: event.config.client,
          auth_type: event.config.auth_type,
        },
      });
    },

    onConnectorLand: async (
      event: ConnectorLandEvent,
      ctx: PluginContext,
    ): Promise<void> => {
      ctx.logger.info(
        `[sap-connector] Landed ${event.records_extracted} rows ` +
          `for ${event.entity} → ${event.bronze_path}`,
      );

      await ctx.audit.log({
        action: 'connector.land.complete',
        actor: 'system',
        resource: `connector:${event.source_system}:${event.entity}`,
        metadata: {
          records_extracted: event.records_extracted,
          files_written: event.files_written,
          bronze_path: event.bronze_path,
        },
      });

      // Emit a Studio notification so the data ops team can see landing status
      await ctx.notify({
        type: 'connector_land',
        title: `SAP ${event.entity} landed`,
        body: `${event.records_extracted.toLocaleString()} rows written to ${event.bronze_path}`,
        severity: 'info',
      });
    },

    onConnectorPromote: async (
      event: ConnectorPromoteEvent,
      ctx: PluginContext,
    ): Promise<void> => {
      ctx.logger.info(
        `[sap-connector] Bronze→Silver promotion ready for: ${event.entities.join(', ')}`,
      );

      await ctx.audit.log({
        action: 'connector.promote.ready',
        actor: 'system',
        resource: `connector:${event.source_system}`,
        metadata: {
          entities: event.entities,
          bronze_root: event.bronze_root,
          silver_root: event.silver_root,
          ready_for_dbt: event.ready_for_dbt,
        },
      });

      if (event.ready_for_dbt) {
        await ctx.notify({
          type: 'connector_promote',
          title: 'SAP bronze zone ready',
          body: `${event.entities.length} entities promoted — run dbt to materialise silver/gold.`,
          severity: 'success',
          action: { label: 'Run dbt', href: '/delivery?trigger=dbt' },
        });
      }
    },
  },
};

export default sapConnectorPlugin;
