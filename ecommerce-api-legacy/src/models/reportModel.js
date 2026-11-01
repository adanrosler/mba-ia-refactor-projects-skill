const { PAYMENT_STATUS } = require('./paymentModel');

const UNKNOWN_STUDENT = 'Unknown';

function buildReport(rows) {
    const byCourse = new Map();
    for (const row of rows) {
        if (!byCourse.has(row.course_id)) {
            byCourse.set(row.course_id, { course: row.title, revenue: 0, students: [] });
        }
        if (row.enrollment_id === null) continue;

        const courseData = byCourse.get(row.course_id);
        if (row.payment_status === PAYMENT_STATUS.PAID) {
            courseData.revenue += row.payment_amount;
        }
        courseData.students.push({
            student: row.user_name ?? UNKNOWN_STUDENT,
            paid: row.payment_amount ?? 0,
        });
    }
    return [...byCourse.values()];
}

function createReportModel(db) {
    return {
        async financialReport({ limit, offset } = {}) {
            const paginated = limit !== undefined;
            const coursesSource = paginated
                ? '(SELECT * FROM courses ORDER BY id LIMIT ? OFFSET ?)'
                : 'courses';
            const rows = await db.all(`
                SELECT c.id AS course_id, c.title, e.id AS enrollment_id, u.name AS user_name,
                       p.amount AS payment_amount, p.status AS payment_status
                FROM ${coursesSource} c
                LEFT JOIN enrollments e ON e.course_id = c.id
                LEFT JOIN users u ON u.id = e.user_id
                LEFT JOIN payments p ON p.id = (
                    SELECT MIN(id) FROM payments WHERE enrollment_id = e.id
                )
                ORDER BY c.id, e.id
            `, paginated ? [limit, offset] : []);
            return buildReport(rows);
        },
    };
}

module.exports = { createReportModel };
