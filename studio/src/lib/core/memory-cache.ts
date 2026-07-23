/**
 * Process-wide in-memory TTL cache for server-side Core loaders.
 * Survives across requests in the same Node process (dev + prod).
 */

const store = new Map<string, { expires: number; value: unknown }>();

export const FORGE_CACHE_TTL_MS =
  process.env.NODE_ENV === 'production' ? 300_000 : 60_000;

export async function cached<T>(
  key: string,
  ttlMs: number,
  fn: () => Promise<T> | T,
): Promise<T> {
  const hit = store.get(key);
  if (hit && hit.expires > Date.now()) {
    return hit.value as T;
  }

  const value = await fn();
  store.set(key, { expires: Date.now() + ttlMs, value });
  return value;
}

export function invalidateCache(prefix?: string): void {
  if (!prefix) {
    store.clear();
    return;
  }

  for (const key of store.keys()) {
    if (key.startsWith(prefix)) {
      store.delete(key);
    }
  }
}
