const express = require('express');
const { loadConfig } = require('./config');
const { createLogger } = require('./utils/logger');
const { createDatabase } = require('./database/connection');
const { initDatabase } = require('./database/seed');
const { createUserModel } = require('./models/userModel');
const { createCourseModel } = require('./models/courseModel');
const { createEnrollmentModel } = require('./models/enrollmentModel');
const { createPaymentModel } = require('./models/paymentModel');
const { createAuditLogModel } = require('./models/auditLogModel');
const { createReportModel } = require('./models/reportModel');
const { createPaymentService } = require('./services/paymentService');
const { createCacheService } = require('./services/cacheService');
const { createCheckoutController } = require('./controllers/checkoutController');
const { createReportController } = require('./controllers/reportController');
const { createUserController } = require('./controllers/userController');
const { createCheckoutRoutes } = require('./routes/checkoutRoutes');
const { createAdminRoutes } = require('./routes/adminRoutes');
const { createUserRoutes } = require('./routes/userRoutes');
const { requireAdmin } = require('./middlewares/auth');
const { createErrorHandler } = require('./middlewares/errorHandler');

// Composition root: cria dependências, injeta nas camadas e sobe o servidor.
async function main() {
    const config = loadConfig();
    const logger = createLogger(config.logLevel);

    const db = createDatabase(config.dbFile);
    await initDatabase(db);
    const transaction = (work) => db.transaction(work);

    const models = {
        userModel: createUserModel(db),
        courseModel: createCourseModel(db),
        enrollmentModel: createEnrollmentModel(db),
        paymentModel: createPaymentModel(db),
        auditLogModel: createAuditLogModel(db),
        reportModel: createReportModel(db),
    };
    const services = {
        paymentService: createPaymentService({ gatewayKey: config.paymentGatewayKey, logger }),
        cacheService: createCacheService({ logger }),
    };
    const controllers = {
        checkoutController: createCheckoutController({ transaction, models, services }),
        reportController: createReportController({ models }),
        userController: createUserController({ transaction, models }),
    };

    if (!config.adminToken) {
        logger.warn('ADMIN_TOKEN não definido; rotas protegidas responderão 401 até ser configurado');
    }
    const adminOnly = requireAdmin(config.adminToken);

    const app = express();
    app.use(express.json());
    app.use('/api', createCheckoutRoutes(controllers));
    app.use('/api', createAdminRoutes({ ...controllers, requireAdmin: adminOnly }));
    app.use('/api', createUserRoutes({ ...controllers, requireAdmin: adminOnly }));
    app.use(createErrorHandler({ logger }));

    app.listen(config.port, config.host, () => {
        logger.info(`Frankenstein LMS rodando em http://${config.host}:${config.port}`);
    });
}

main().catch((err) => {
    process.stderr.write(`Falha ao iniciar a aplicação: ${err.stack || err}\n`);
    process.exit(1);
});
