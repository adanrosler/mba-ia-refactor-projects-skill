const crypto = require('crypto');
const { unauthorized } = require('../errors/HttpError');

// Exige `Authorization: Bearer <ADMIN_TOKEN>` somente quando o token está configurado.
function createRequireAdmin(adminToken) {
    const expected = adminToken ? Buffer.from(adminToken) : null;

    return (req, res, next) => {
        if (!expected) return next();
        const sent = Buffer.from((req.get('authorization') || '').replace(/^Bearer /, ''));
        const valid = sent.length === expected.length && crypto.timingSafeEqual(sent, expected);
        return valid ? next() : next(unauthorized());
    };
}

module.exports = { createRequireAdmin };
