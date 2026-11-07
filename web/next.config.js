/** @type {import('next').NextConfig} */
const nextConfig = {
  // Phase 6F: standalone output for a minimal production server image.
  // The rewrite target is server-side only (MYFARMAI_API_ORIGIN). Don't use
  // NEXT_PUBLIC_API_BASE_URL here: dev sets it to a RELATIVE /api/v1 in
  // .env.local so the client calls stay same-origin (cookies work); a
  // relative destination would make this proxy silently fail.
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: `${
          process.env.MYFARMAI_API_ORIGIN || 'http://localhost:8000/api/v1'
        }/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;