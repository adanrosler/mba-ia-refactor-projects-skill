function createUserModel(db) {
    return {
        async findIdByEmail(email) {
            const row = await db.get('SELECT id FROM users WHERE email = ?', [email]);
            return row ? row.id : null;
        },
        async create({ name, email, passwordHash }) {
            const { lastID } = await db.run(
                'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [name, email, passwordHash]);
            return lastID;
        },
        async deleteById(id) {
            const { changes } = await db.run('DELETE FROM users WHERE id = ?', [id]);
            return changes;
        },
    };
}

module.exports = { createUserModel };
