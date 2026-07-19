import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  poweredByHeader: false,
  reactStrictMode: true,
  // Keep Prisma out of the bundler so query engines resolve on Vercel.
  serverExternalPackages: ["@prisma/client", "prisma", "bcryptjs"],
  outputFileTracingIncludes: {
    "/**": [
      "./node_modules/.prisma/**/*",
      "./node_modules/@prisma/client/**/*",
    ],
  },
  experimental: {
    serverActions: {
      bodySizeLimit: "2mb",
    },
  },
  images: {
    remotePatterns: [],
  },
};

export default nextConfig;
