const USER_DELETED_MESSAGE = 'Usuário deletado, junto com suas matrículas e pagamentos.';

function createUserController({ transaction, models }) {
    const { userModel, enrollmentModel, paymentModel } = models;

    return {
        async deleteUser(id) {
            // Remove dependentes e usuário atomicamente: nenhum registro órfão.
            await transaction(async () => {
                await paymentModel.deleteByUserId(id);
                await enrollmentModel.deleteByUserId(id);
                await userModel.deleteById(id);
            });
            return USER_DELETED_MESSAGE;
        },
    };
}

module.exports = { createUserController };
