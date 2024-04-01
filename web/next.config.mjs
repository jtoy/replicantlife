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
            NEXT_PUBLIC_CONTENT_DIRECTORY: ''
        },   
    };
} else {
    nextConfig = {
        env: {
            NEXT_PUBLIC_BASE_PATH: '',
            NEXT_PUBLIC_CONTENT_DIRECTORY: ''
        }
    };
}

export default nextConfig;
