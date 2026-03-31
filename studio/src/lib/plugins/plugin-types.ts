/**
 * Plugin Types — Shared interfaces for the extension SDK.
 */

import type { TypedPluginHook } from './hook-contracts';
import type { PluginLifecycle } from './lifecycle';

export type PluginType = 'tool' | 'widget' | 'datasource';
export type PluginHook = TypedPluginHook;

export interface PluginManifest {
  id: string;
  name: string;
  version: string;
  author: string;
  type: PluginType;
  description: string;
  entrypoint: string;
  hooks?: PluginHook[];
  lifecycle?: PluginLifecycle;
}

export interface RegisteredPlugin {
  manifest: PluginManifest;
  enabled: boolean;
  registeredAt: number;
}
