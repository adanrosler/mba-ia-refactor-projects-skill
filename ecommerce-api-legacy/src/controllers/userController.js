function createUserController({ models, withTransaction }) {
    const { users, enrollments, payments } = models;

    return {
        async deleteUser(id) {
            await withTransaction(async () => {
                await payments.deleteByUser(id);
                await enrollments.deleteByUser(id);
                await users.deleteById(id);
            });
            return 'Usuário deletado';
        },
    };
}

module.exports = { createUserController };
