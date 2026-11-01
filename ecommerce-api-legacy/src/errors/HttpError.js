class HttpError extends Error {
    constructor(status, message) {
        super(message);
        this.name = 'HttpError';
        this.status = status;
    }
}

const badRequest = (message = 'Bad Request') => new HttpError(400, message);
const notFound = (message) => new HttpError(404, message);
const unauthorized = (message = 'Não autorizado') => new HttpError(401, message);

module.exports = { HttpError, badRequest, notFound, unauthorized };
