import { defineConfig } from 'vitest/config';
import path from 'node:path';

export default defineConfig({
  test: {
    environment: 'jsdom',
    include: ['tests/**/*.test.ts', 'tests/**/*.test.tsx'],
    globals: true,
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
      // Stub optional cloud SDK packages so Vitest does not fail on missing
      // peer dependencies.  Tests that exercise these adapters use vi.doMock
      // to replace the stubs with controlled implementations.
      '@azure/keyvault-secrets': path.resolve(
        __dirname,
        'src/lib/secrets/_stubs/azure-kv-stub.js',
      ),
      '@azure/identity': path.resolve(
        __dirname,
        'src/lib/secrets/_stubs/azure-identity-stub.js',
      ),
      '@aws-sdk/client-secrets-manager': path.resolve(
        __dirname,
        'src/lib/secrets/_stubs/aws-sm-stub.js',
      ),
    },
  },
});
