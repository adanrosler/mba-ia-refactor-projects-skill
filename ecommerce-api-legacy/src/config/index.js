const toInt = (value, fallback) => {
    const parsed = Number.parseInt(value, 10);
    return Number.isInteger(parsed) ? parsed : fallback;
};

const config = Object.freeze({
    port: toInt(process.env.PORT, 3000),
    host: process.env.HOST || '127.0.0.1',
    databaseFile: process.env.DATABASE_FILE || ':memory:',
    // Sem chave configurada o gateway opera em modo simulado.
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
    // Sem token configurado as rotas administrativas ficam abertas (compatibilidade) e um aviso é logado.
    adminToken: process.env.ADMIN_TOKEN,
    logLevel: process.env.LOG_LEVEL || 'info',
});

module.exports = config;
