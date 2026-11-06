const { validateCheckout } = require('../validators/checkoutValidator');
const { badRequest, notFound } = require('../errors/HttpError');
const { PAYMENT_STATUS } = require('../models/paymentModel');
const { hashPassword, generateRandomPassword } = require('../utils/password');

function createCheckoutController({ transaction, models, services }) {
    const { userModel, courseModel, enrollmentModel, paymentModel, auditLogModel } = models;
    const { paymentService, cacheService } = services;

    async function findOrCreateUser({ name, email, password }) {
        const existingId = await userModel.findIdByEmail(email);
        if (existingId) return existingId;
        const passwordHash = await hashPassword(password || generateRandomPassword());
        return userModel.create({ name, email, passwordHash });
    }

    return {
        async checkout(body) {
            const order = validateCheckout(body);

            const course = await courseModel.findActiveById(order.courseId);
            if (!course) throw notFound('Curso não encontrado');

            const paymentStatus = paymentService.charge(order.card);
            if (paymentStatus !== PAYMENT_STATUS.PAID) throw badRequest('Pagamento recusado');

            const { userId, enrollmentId } = await transaction(async () => {
                const buyerId = await findOrCreateUser(order);
                const newEnrollmentId = await enrollmentModel.create({ userId: buyerId, courseId: course.id });
                await paymentModel.create({ enrollmentId: newEnrollmentId, amount: course.price, status: paymentStatus });
                await auditLogModel.record(`Checkout curso ${course.id} por ${buyerId}`);
                return { userId: buyerId, enrollmentId: newEnrollmentId };
            });

            cacheService.set(`last_checkout_${userId}`, course.title);
            return { msg: 'Sucesso', enrollment_id: enrollmentId };
        },
    };
}

module.exports = { createCheckoutController };
