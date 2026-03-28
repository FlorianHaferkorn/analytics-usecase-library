/**
 * Plugin Types — Shared interfaces for the extension SDK.
 */

export type PluginType = 'tool' | 'widget' | 'datasource';
export type PluginHook = 'onBracketLoad' | 'onKpiEvaluate' | 'onThemeChange';

export interface PluginManifest {
  id: string;
  name: string;
  version: string;
  author: string;
  type: PluginType;
  description: string;
  entrypoint: string;
  hooks?: PluginHook[];
}

export interface RegisteredPlugin {
  manifest: PluginManifest;
  enabled: boolean;
  registeredAt: number;
}
