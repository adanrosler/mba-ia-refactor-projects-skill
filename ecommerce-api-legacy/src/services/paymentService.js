const { PAYMENT_STATUS } = require('../models/paymentModel');

const APPROVED_CARD_PREFIX = '4';
const VISIBLE_CARD_DIGITS = 4;

const maskCard = (card) => `****${card.slice(-VISIBLE_CARD_DIGITS)}`;

function createPaymentService({ gatewayKey, logger }) {
    if (!gatewayKey) logger.warn('PAYMENT_GATEWAY_KEY não definida; gateway de pagamento em modo simulado');

    return {
        // Simulação do gateway: cartões iniciados em "4" são aprovados.
        charge(card, amount) {
            logger.info(`Processando pagamento de ${amount} no cartão ${maskCard(card)}`);
            return card.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
        },
    };
}

module.exports = { createPaymentService, maskCard };
