function createReportModel(db) {
    return {
        // Uma única query (sem N+1): cada curso com suas matrículas, aluno e primeiro pagamento.
        findCourseEnrollmentRows() {
            return db.all(`
                SELECT c.id AS courseId, c.title AS courseTitle,
                       e.id AS enrollmentId, u.name AS studentName,
                       p.amount AS paymentAmount, p.status AS paymentStatus
                  FROM courses c
             LEFT JOIN enrollments e ON e.course_id = c.id
             LEFT JOIN users u ON u.id = e.user_id
             LEFT JOIN payments p ON p.id = (
                       SELECT MIN(p2.id) FROM payments p2 WHERE p2.enrollment_id = e.id)
              ORDER BY c.id, e.id`);
        },
    };
}

module.exports = { createReportModel };
