const express = require('express');
const { asyncHandler } = require('../middlewares/asyncHandler');

function createUserRoutes({ userController, requireAdmin }) {
    const router = express.Router();

    router.delete('/users/:id', requireAdmin, asyncHandler(async (req, res) => {
        res.send(await userController.deleteUser(req.params.id));
    }));

    return router;
}

module.exports = { createUserRoutes };
