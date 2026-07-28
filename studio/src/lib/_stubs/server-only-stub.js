/**
 * Test stub for Next.js's `server-only` marker.
 *
 * `server-only` has no runtime behaviour — importing it makes the bundler fail the build
 * if a server module is pulled into a client bundle. Vitest has no such notion and no
 * such package installed, so the import would abort the whole test file before a single
 * assertion ran (this is what kept the four `tests/lib/*-loader` suites from loading).
 *
 * Aliased in `vitest.config.ts` only. The real guard still applies to `next build`.
 */
export {};
