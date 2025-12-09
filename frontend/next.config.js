/** @type {import('next').NextConfig} */
const nextConfig = {
  // No rewrites needed - Vercel handles /api routes via serverless functions
  // For local development, run the backend separately on port 8000
  async rewrites() {
    // Only proxy in development when running locally
    if (process.env.NODE_ENV === 'development' && process.env.LOCAL_DEV === 'true') {
      return [
        {
          source: '/api/:path*',
          destination: 'http://localhost:8000/api/:path*',
        },
      ];
    }
    return [];
  },
};

module.exports = nextConfig;
