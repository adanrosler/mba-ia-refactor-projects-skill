function createEnrollmentModel(db) {
    return {
        async create(userId, courseId) {
            const { lastID } = await db.run(
                'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
                [userId, courseId],
            );
            return lastID;
        },

        async deleteByUser(userId) {
            await db.run('DELETE FROM enrollments WHERE user_id = ?', [userId]);
        },
    };
}

module.exports = { createEnrollmentModel };
