function createCacheService({ logger }) {
    const store = new Map();

    return {
        set(key, value) {
            logger.debug('Salvando no cache', { key });
            store.set(key, value);
        },
        get(key) {
            return store.get(key);
        },
    };
}

module.exports = { createCacheService };
