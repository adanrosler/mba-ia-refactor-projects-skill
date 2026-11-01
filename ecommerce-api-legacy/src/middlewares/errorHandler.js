const { HttpError } = require('../errors/HttpError');

const CLIENT_ERROR_MIN = 400;
const SERVER_ERROR_MIN = 500;

function createErrorHandler(logger) {
    // eslint-disable-next-line no-unused-vars
    return (err, req, res, next) => {
        if (err instanceof HttpError) return res.status(err.status).send(err.message);

        // Erros do body parser (JSON malformado, payload grande etc.).
        if (err.status >= CLIENT_ERROR_MIN && err.status < SERVER_ERROR_MIN) {
            return res.status(err.status).send('Bad Request');
        }

        logger.error(`${req.method} ${req.originalUrl} falhou:`, err);
        return res.status(500).send('Erro interno do servidor');
    };
}

module.exports = { createErrorHandler };
