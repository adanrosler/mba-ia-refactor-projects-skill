const express = require('express');
const config = require('./config');
const { createLogger } = require('./utils/logger');
const { createConnection } = require('./database/connection');
const { initSchema, seed } = require('./database/seed');
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
const { createRequireAdmin } = require('./middlewares/auth');
const { createErrorHandler } = require('./middlewares/errorHandler');

const logger = createLogger(config.logLevel);

async function bootstrap() {
    const db = await createConnection(config.databaseFile);
    await initSchema(db);
    await seed(db);

    const models = {
        users: createUserModel(db),
        courses: createCourseModel(db),
        enrollments: createEnrollmentModel(db),
        payments: createPaymentModel(db),
        auditLogs: createAuditLogModel(db),
        reports: createReportModel(db),
    };
    const services = {
        payment: createPaymentService({ gatewayKey: config.paymentGatewayKey, logger }),
        cache: createCacheService({ logger }),
    };
    const { withTransaction } = db;

    if (!config.adminToken) logger.warn('ADMIN_TOKEN não definida; rotas administrativas sem autenticação');
    const requireAdmin = createRequireAdmin(config.adminToken);

    const app = express();
    app.use(express.json());
    app.use('/api', createCheckoutRoutes(createCheckoutController({ models, services, withTransaction })));
    app.use('/api', createAdminRoutes(createReportController({ models }), requireAdmin));
    app.use('/api', createUserRoutes(createUserController({ models, withTransaction }), requireAdmin));
    app.use(createErrorHandler(logger));

    app.listen(config.port, config.host, () => {
        logger.info(`LMS API rodando em http://${config.host}:${config.port}`);
    });
}

bootstrap().catch((err) => {
    logger.error('Falha ao iniciar a aplicação:', err);
    process.exitCode = 1;
});
