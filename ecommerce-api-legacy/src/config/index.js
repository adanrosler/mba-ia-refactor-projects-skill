const DEFAULT_PORT = 3000;
const DEFAULT_HOST = '127.0.0.1';

function parsePort(value) {
    const port = Number.parseInt(value, 10);
    return Number.isInteger(port) && port > 0 ? port : DEFAULT_PORT;
}

function loadConfig(env = process.env) {
    return Object.freeze({
        port: parsePort(env.PORT),
        host: env.HOST || DEFAULT_HOST,
        dbFile: env.DB_FILE || ':memory:',
        adminToken: env.ADMIN_TOKEN || undefined,
        paymentGatewayKey: env.PAYMENT_GATEWAY_KEY || undefined,
        logLevel: env.LOG_LEVEL || 'info',
    });
}

module.exports = { loadConfig };
