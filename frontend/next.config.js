/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    domains: ['localhost'],
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
        pathname: '/temp_images/**',
      },
      {
        protocol: 'https',
        hostname: '**.replicate.delivery',
        pathname: '/**',
      },
    ],
  },
};

module.exports = nextConfig;