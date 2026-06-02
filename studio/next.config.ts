import type { NextConfig } from 'next';

/**
 * Backward-compatible rewrites for the tenant-scoped API routes introduced in v0.2.
 *
 * Old URL pattern:  /api/core/*  /api/governance/*  /api/export/*
 * New URL pattern:  /api/projects/default/<sub-path>
 *
 * These rewrites are present for 1 minor version.  Clients should migrate to
 * the explicit /api/projects/[projectId]/... URLs.
 */
const COMPAT_PREFIXES = ['core', 'governance', 'export'] as const;

const nextConfig: NextConfig = {
  output: 'standalone',
  turbopack: {
    root: __dirname,
    // Resolve optional cloud-SDK packages to no-op stubs at build time.
    // These packages are only available at runtime when installed.
    resolveAlias: {
      '@azure/keyvault-secrets': './src/lib/secrets/_stubs/azure-kv-stub.js',
      '@azure/identity': './src/lib/secrets/_stubs/azure-identity-stub.js',
      '@aws-sdk/client-secrets-manager': './src/lib/secrets/_stubs/aws-sm-stub.js',
    },
  },
  // Treat optional cloud-SDK packages and the native sqlite module as
  // server-side externals so the bundler does not attempt to bundle them.
  serverExternalPackages: [
    'better-sqlite3',
    '@azure/keyvault-secrets',
    '@azure/identity',
    '@aws-sdk/client-secrets-manager',
  ],
  async rewrites() {
    return COMPAT_PREFIXES.flatMap((prefix) => [
      {
        source: `/api/${prefix}/:path*`,
        destination: `/api/projects/default/${prefix}/:path*`,
      },
    ]);
  },
  async redirects() {
    return [
      { source: '/catalog', destination: '/library?tab=kpis', permanent: false },
      { source: '/catalog/:kpiId', destination: '/detail/kpi/:kpiId', permanent: false },
      { source: '/registry/brackets/:id', destination: '/detail/usecase/:id', permanent: false },
      { source: '/steering', destination: '/overview', permanent: false },
      { source: '/discover', destination: '/overview', permanent: false },
      { source: '/blueprint', destination: '/canvas', permanent: false },
      { source: '/compose', destination: '/library', permanent: false },
      { source: '/generate', destination: '/delivery', permanent: false },
      { source: '/brand', destination: '/templates', permanent: false },
      { source: '/brand-lab', destination: '/templates', permanent: false },
      { source: '/lineage', destination: '/canvas', permanent: false },
      { source: '/drift', destination: '/registry/health', permanent: false },
      { source: '/dashboard', destination: '/overview', permanent: false },
    ];
  },
};

export default nextConfig;
