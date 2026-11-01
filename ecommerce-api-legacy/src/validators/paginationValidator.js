const { badRequest } = require('../errors/HttpError');

const toNonNegativeInt = (value) => {
    if (!/^\d+$/.test(String(value))) throw badRequest();
    return Number(value);
};

// Paginação opcional: sem `limit`, devolve a lista completa (comportamento original).
function parsePagination(query = {}) {
    if (query.limit === undefined) return {};
    return {
        limit: toNonNegativeInt(query.limit),
        offset: query.offset === undefined ? 0 : toNonNegativeInt(query.offset),
    };
}

module.exports = { parsePagination };
