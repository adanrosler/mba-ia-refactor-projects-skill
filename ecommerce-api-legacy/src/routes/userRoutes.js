const express = require('express');
const { asyncHandler } = require('../middlewares/asyncHandler');

function createUserRoutes(controller, requireAdmin) {
    const router = express.Router();
    router.delete('/users/:id', requireAdmin, asyncHandler(async (req, res) => {
        res.send(await controller.deleteUser(req.params.id));
    }));
    return router;
}

module.exports = { createUserRoutes };
