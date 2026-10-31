/** @type {import('next').NextConfig} */
const nextConfig = {
  // Phase 6F: standalone output for a minimal production server image.
  // NEXT_PUBLIC_API_BASE_URL is baked into the rewrite at BUILD time —
  // set it before `npm run build` (documented in docs/backend/API.md).
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1'}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;