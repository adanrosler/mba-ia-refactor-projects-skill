const crypto = require('crypto');

const BEARER_PREFIX = /^Bearer /;

// Fail-closed: nega quando o token falta, não confere ou ADMIN_TOKEN não está configurado.
function requireAdmin(adminToken) {
    return (req, res, next) => {
        const sent = (req.get('authorization') || '').replace(BEARER_PREFIX, '');
        const authorized = Boolean(adminToken) && Boolean(sent)
            && sent.length === adminToken.length
            && crypto.timingSafeEqual(Buffer.from(sent), Buffer.from(adminToken));
        return authorized ? next() : res.status(401).json({ error: 'Não autorizado' });
    };
}

module.exports = { requireAdmin };
