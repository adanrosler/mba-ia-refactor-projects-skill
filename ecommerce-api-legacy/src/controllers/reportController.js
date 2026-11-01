const { parsePagination } = require('../validators/paginationValidator');

function createReportController({ models }) {
    return {
        financialReport(query) {
            return models.reports.financialReport(parsePagination(query));
        },
    };
}

module.exports = { createReportController };
