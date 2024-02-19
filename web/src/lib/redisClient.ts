import { Redis } from 'ioredis';
let redis: Redis | undefined = undefined;

export const getRedisClient = (): Redis => {
    if(!redis) {
        redis = new Redis(process.env.REDIS_URL as string);
    }
    return redis;
};