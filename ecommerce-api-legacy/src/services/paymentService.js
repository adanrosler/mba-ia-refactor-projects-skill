const { PAYMENT_STATUS } = require('../models/paymentModel');

// Regra do gateway simulado: cartões iniciados em "4" são aprovados.
const APPROVED_CARD_PREFIX = '4';
const VISIBLE_CARD_DIGITS = 4;

function maskCard(card) {
    return `****${card.slice(-VISIBLE_CARD_DIGITS)}`;
}

function createPaymentService({ gatewayKey, logger }) {
    if (!gatewayKey) {
        logger.warn('PAYMENT_GATEWAY_KEY não definido; gateway de pagamento em modo simulado');
    }

    return {
        charge(card) {
            logger.info('Processando pagamento', { card: maskCard(card), simulated: !gatewayKey });
            return card.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
        },
    };
}

module.exports = { createPaymentService };
