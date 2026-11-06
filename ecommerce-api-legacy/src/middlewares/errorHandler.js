const { HttpError } = require('../errors/HttpError');

// Mantém o contrato original: erros respondem texto puro com o mesmo status/mensagem.
function createErrorHandler({ logger }) {
    // A assinatura com 4 parâmetros é o que faz o Express tratar isto como middleware de erro.
    return (err, req, res, next) => { // eslint-disable-line no-unused-vars
        if (err instanceof HttpError) return res.status(err.status).send(err.message);
        if (err.type === 'entity.parse.failed') return res.status(400).send('Bad Request');

        logger.error('Erro não tratado', { method: req.method, path: req.path, error: err.message });
        return res.status(500).send('Erro interno do servidor');
    };
}

module.exports = { createErrorHandler };
