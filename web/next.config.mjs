/* esline-env node */
/** @type {import('next').NextConfig} */
let nextConfig = {};

if (process.env.NODE_ENV === 'production') {
    nextConfig = {
        output: 'export',
        basePath: '/replay',
        assetPrefix: '/replay',
        env: {
            NEXT_PUBLIC_BASE_PATH: '/replay',
        },   
    };
} else {
    nextConfig = {
        env: {
            NEXT_PUBLIC_BASE_PATH: ''
        }
    };
}

export default nextConfig;
