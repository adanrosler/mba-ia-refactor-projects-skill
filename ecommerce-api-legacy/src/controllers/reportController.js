const { PAYMENT_STATUS } = require('../models/paymentModel');

const UNKNOWN_STUDENT = 'Unknown';

function createReportController({ models }) {
    const { reportModel } = models;

    return {
        async financialReport() {
            const rows = await reportModel.findCourseEnrollmentRows();
            const byCourse = new Map();

            for (const row of rows) {
                if (!byCourse.has(row.courseId)) {
                    byCourse.set(row.courseId, { course: row.courseTitle, revenue: 0, students: [] });
                }
                if (row.enrollmentId === null) continue;

                const courseData = byCourse.get(row.courseId);
                if (row.paymentStatus === PAYMENT_STATUS.PAID) courseData.revenue += row.paymentAmount;
                courseData.students.push({
                    student: row.studentName ?? UNKNOWN_STUDENT,
                    paid: row.paymentAmount ?? 0,
                });
            }

            return [...byCourse.values()];
        },
    };
}

module.exports = { createReportController };
