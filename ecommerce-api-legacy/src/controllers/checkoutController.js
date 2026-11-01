const { validateCheckout } = require('../validators/checkoutValidator');
const { notFound, badRequest } = require('../errors/HttpError');
const { PAYMENT_STATUS } = require('../models/paymentModel');
const { hashPassword, generateRandomPassword } = require('../utils/password');

function createCheckoutController({ models, services, withTransaction }) {
    const { users, courses, enrollments, payments, auditLogs } = models;
    const { payment, cache } = services;

    return {
        async checkout(body) {
            const input = validateCheckout(body);

            const course = await courses.findActiveById(input.courseId);
            if (!course) throw notFound('Curso não encontrado');

            const status = payment.charge(input.card, course.price);
            if (status === PAYMENT_STATUS.DENIED) throw badRequest('Pagamento recusado');

            const { userId, enrollmentId } = await withTransaction(async () => {
                const existing = await users.findByEmail(input.email);
                const id = existing
                    ? existing.id
                    : await users.create({
                        name: input.name,
                        email: input.email,
                        passwordHash: await hashPassword(input.password || generateRandomPassword()),
                    });
                const newEnrollmentId = await enrollments.create(id, input.courseId);
                await payments.create(newEnrollmentId, course.price, status);
                await auditLogs.record(`Checkout curso ${input.courseId} por ${id}`);
                return { userId: id, enrollmentId: newEnrollmentId };
            });

            cache.set(`last_checkout_${userId}`, course.title);
            return { msg: 'Sucesso', enrollment_id: enrollmentId };
        },
    };
}

module.exports = { createCheckoutController };
