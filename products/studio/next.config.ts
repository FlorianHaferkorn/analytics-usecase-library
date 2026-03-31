import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow the API routes to read files from the repo root
  serverExternalPackages: ["js-yaml"],
};

export default nextConfig;
