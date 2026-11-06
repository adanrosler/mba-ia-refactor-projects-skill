const LEVELS = { debug: 10, info: 20, warn: 30, error: 40 };

function createLogger(level = 'info') {
    const threshold = LEVELS[level] ?? LEVELS.info;
    const write = (name) => (message, meta) => {
        if (LEVELS[name] < threshold) return;
        const line = `[${new Date().toISOString()}] ${name.toUpperCase()} ${message}`;
        const stream = LEVELS[name] >= LEVELS.warn ? process.stderr : process.stdout;
        stream.write(meta === undefined ? `${line}\n` : `${line} ${JSON.stringify(meta)}\n`);
    };
    return { debug: write('debug'), info: write('info'), warn: write('warn'), error: write('error') };
}

module.exports = { createLogger };
