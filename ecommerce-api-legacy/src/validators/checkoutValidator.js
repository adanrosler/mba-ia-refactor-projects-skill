const { badRequest } = require('../errors/HttpError');

const isNonEmptyString = (value) => typeof value === 'string' && value.length > 0;

// Chaves públicas do contrato: usr, eml, pwd (opcional), c_id, card.
function validateCheckout(body) {
    if (!body || typeof body !== 'object') throw badRequest();

    const { usr: name, eml: email, pwd: password, c_id: courseId, card } = body;
    if (!name || !email || !courseId || !card) throw badRequest();
    if (!isNonEmptyString(name) || !isNonEmptyString(email) || !isNonEmptyString(card)) throw badRequest();
    if (password !== undefined && password !== null && typeof password !== 'string') throw badRequest();

    return { name, email, password: password || null, courseId, card };
}

module.exports = { validateCheckout };
