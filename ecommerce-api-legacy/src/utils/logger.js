const LEVELS = { error: 0, warn: 1, info: 2, debug: 3 };

function createLogger(level = 'info') {
    const threshold = LEVELS[level] ?? LEVELS.info;
    const write = (name, method) => (...args) => {
        if (LEVELS[name] <= threshold) method(`[${name.toUpperCase()}]`, ...args);
    };
    return {
        error: write('error', console.error),
        warn: write('warn', console.warn),
        info: write('info', console.log),
        debug: write('debug', console.log),
    };
}

module.exports = { createLogger };
