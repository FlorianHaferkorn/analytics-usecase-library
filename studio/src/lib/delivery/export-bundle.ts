/** Build a real delivery archive while preserving target artifact paths. */

import { strToU8, zipSync } from 'fflate';

export interface DeliveryFile {
  filename: string;
  content: string;
}

function safeArchivePath(filename: string): string {
  const normalized = filename.replace(/\\/g, '/').replace(/^\.\//, '');
  const parts = normalized.split('/');
  if (!normalized || normalized.startsWith('/') || parts.some((part) => !part || part === '..')) {
    throw new Error(`Unsafe delivery artifact path: ${filename}`);
  }
  return normalized;
}

export function buildDeliveryZip(files: readonly DeliveryFile[], reproducible = false): Uint8Array {
  if (files.length === 0) throw new Error('No validated artifacts available for download');
  const archive: Record<string, Uint8Array> = {};
  for (const file of files) {
    const path = safeArchivePath(file.filename);
    if (path in archive) throw new Error(`Duplicate delivery artifact path: ${path}`);
    archive[path] = strToU8(file.content);
  }
  return zipSync(archive, { level: 6, ...(reproducible ? {mtime: new Date(1980, 0, 1)} : {}) });
}
