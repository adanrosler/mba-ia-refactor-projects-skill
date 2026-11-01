const express = require('express');
const { asyncHandler } = require('../middlewares/asyncHandler');

function createAdminRoutes(controller, requireAdmin) {
    const router = express.Router();
    router.get('/admin/financial-report', requireAdmin, asyncHandler(async (req, res) => {
        res.json(await controller.financialReport(req.query));
    }));
    return router;
}

module.exports = { createAdminRoutes };
