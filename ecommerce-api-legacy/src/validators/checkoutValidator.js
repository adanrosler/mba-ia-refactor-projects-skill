const { badRequest } = require('../errors/HttpError');

const isNonEmptyString = (value) => typeof value === 'string' && value.trim() !== '';

function parseId(value) {
    if (Number.isInteger(value) && value > 0) return value;
    if (typeof value === 'string' && /^[1-9]\d*$/.test(value)) return Number(value);
    return null;
}

// Mantém as chaves públicas do contrato (usr, eml, pwd, c_id, card) e devolve nomes internos claros.
function validateCheckout(body) {
    const { usr, eml, pwd, c_id: courseIdInput, card } = body || {};
    const courseId = parseId(courseIdInput);
    const passwordValid = pwd === undefined || pwd === null || typeof pwd === 'string';

    if (!isNonEmptyString(usr) || !isNonEmptyString(eml) || !courseId
        || !isNonEmptyString(card) || !passwordValid) {
        throw badRequest();
    }

    return { name: usr, email: eml, password: pwd || null, courseId, card };
}

module.exports = { validateCheckout };
