/** @type {import('next').NextConfig} */
const nextConfig = {
  // Phase 6F: standalone output for a minimal production server image.
  // The rewrite target is server-side only (MYFARMAI_API_ORIGIN). Don't use
  // NEXT_PUBLIC_API_BASE_URL here: dev sets it to a RELATIVE /api/v1 in
  // .env.local so the client calls stay same-origin (cookies work); a
  // relative destination would make this proxy silently fail.
  output: 'standalone',
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          {
            key: 'Permissions-Policy',
            value: 'geolocation=(self), camera=(), microphone=()',
          },
          { key: 'Strict-Transport-Security', value: 'max-age=31536000' },
        ],
      },
    ];
  },
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: `${
          process.env.MYFARMAI_API_ORIGIN ||
          (process.env.NODE_ENV === 'production'
            ? 'https://myfarmai-backend-50047414881.development.catalystappsail.in/api/v1'
            : 'http://localhost:8000/api/v1')
        }/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;