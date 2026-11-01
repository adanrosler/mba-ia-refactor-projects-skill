const ACTIVE = 1;

function createCourseModel(db) {
    return {
        findActiveById(id) {
            return db.get('SELECT * FROM courses WHERE id = ? AND active = ?', [id, ACTIVE]);
        },
    };
}

module.exports = { createCourseModel };
