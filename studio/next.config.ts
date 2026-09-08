import type { NextConfig } from 'next';
import path from 'node:path';

/**
 * Library APIs remain under /api/core. Project APIs require an explicit project
 * and enforce package authority. Never rewrite library requests to "default".
 */
const BRIDGE_TRACE_EXCLUDES = [
  './next.config.ts',
  './src/**/*',
  './tests/**/*',
  './e2e/**/*',
  './docs/**/*',
  './test-results/**/*',
  './tooling/**/*',
  './data/**/*',
  './*.md',
];

const nextConfig: NextConfig = {
  // Webpack production output and Turbopack development output are deliberately
  // isolated. Reusing one .next directory across both builders caused stale CSS
  // resolution state when a developer started the app after a production build.
  distDir: process.env.NODE_ENV === 'development' ? '.next-dev' : '.next',
  output: 'standalone',
  // Node's file tracer cannot infer the runtime boundary of a dynamic Python
  // subprocess and otherwise copies the repository into every bridge route.
  // The route code is already bundled; Python assets are mounted separately
  // through ALUCA_REPO_ROOT and intentionally stay outside standalone output.
  outputFileTracingExcludes: {
    '/api/delivery-flow': BRIDGE_TRACE_EXCLUDES,
    '/api/generate': BRIDGE_TRACE_EXCLUDES,
    '/api/precore': BRIDGE_TRACE_EXCLUDES,
    '/api/wirkung/attribute': BRIDGE_TRACE_EXCLUDES,
    '/api/wirkung/refinements': BRIDGE_TRACE_EXCLUDES,
  },
  turbopack: {
    // Studio is independently buildable. The governed Python layer is invoked
    // at runtime through ALUCA_REPO_ROOT and must not become part of the Next.js
    // module graph or standalone output trace.
    root: __dirname,
    // Resolve optional cloud-SDK packages to no-op stubs at build time.
    // These packages are only available at runtime when installed.
    resolveAlias: {
      '@azure/keyvault-secrets': './src/lib/secrets/_stubs/azure-kv-stub.js',
      '@azure/identity': './src/lib/secrets/_stubs/azure-identity-stub.js',
      '@aws-sdk/client-secrets-manager': './src/lib/secrets/_stubs/aws-sm-stub.js',
    },
  },
  webpack(config) {
    // Keep the optional secret providers out of local/standalone builds unless
    // their SDKs are deliberately installed in the target environment.
    config.resolve.alias = {
      ...config.resolve.alias,
      '@azure/keyvault-secrets': path.resolve(__dirname, 'src/lib/secrets/_stubs/azure-kv-stub.js'),
      '@azure/identity': path.resolve(__dirname, 'src/lib/secrets/_stubs/azure-identity-stub.js'),
      '@aws-sdk/client-secrets-manager': path.resolve(__dirname, 'src/lib/secrets/_stubs/aws-sm-stub.js'),
    };
    return config;
  },
  // Treat optional cloud-SDK packages and the native sqlite module as
  // server-side externals so the bundler does not attempt to bundle them.
  serverExternalPackages: [
    'better-sqlite3',
    '@azure/keyvault-secrets',
    '@azure/identity',
    '@aws-sdk/client-secrets-manager',
  ],
  async redirects() {
    return [
      { source: '/catalog/:kpiId', destination: '/detail/kpi/:kpiId', permanent: false },
      { source: '/registry/brackets/:id', destination: '/detail/usecase/:id', permanent: false },
      { source: '/brand', destination: '/templates', permanent: false },
      { source: '/brand-lab', destination: '/templates', permanent: false },
      { source: '/lineage', destination: '/canvas', permanent: false },
      { source: '/dashboard', destination: '/overview', permanent: false },
    ];
  },
};

export default nextConfig;
