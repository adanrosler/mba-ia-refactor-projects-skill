from datetime import timedelta

from models.category import Category
from models.task import Task
from models.user import User
from utils.constants import (HIGH_PRIORITY_THRESHOLD, PRIORITY_LABELS, RECENT_ACTIVITY_DAYS,
                             STATUS_CANCELLED, STATUS_DONE, STATUS_IN_PROGRESS, STATUS_PENDING)
from utils.errors import NotFoundError
from utils.stats import completion_rate
from utils.time import utcnow


class ReportController:
    def summary(self):
        now = utcnow()
        by_status = Task.count_by_status()
        by_priority = Task.count_by_priority()
        overdue_tasks = Task.list_overdue(now)
        since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
        totals_by_user = Task.totals_by_user()

        user_productivity = []
        for user in User.list():
            total, completed = totals_by_user.get(user.id, (0, 0))
            user_productivity.append({
                'user_id': user.id,
                'user_name': user.name,
                'total_tasks': total,
                'completed_tasks': completed,
                'completion_rate': completion_rate(completed, total),
            })

        return {
            'generated_at': str(now),
            'overview': {
                'total_tasks': Task.count(),
                'total_users': User.count(),
                'total_categories': Category.count(),
            },
            'tasks_by_status': {
                status: by_status.get(status, 0)
                for status in (STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED)
            },
            'tasks_by_priority': {label: by_priority.get(level, 0) for level, label in PRIORITY_LABELS.items()},
            'overdue': {
                'count': len(overdue_tasks),
                'tasks': [
                    {'id': task.id, 'title': task.title, 'due_date': str(task.due_date),
                     'days_overdue': task.days_overdue(now)}
                    for task in overdue_tasks
                ],
            },
            'recent_activity': {
                'tasks_created_last_7_days': Task.count_created_since(since),
                'tasks_completed_last_7_days': Task.count_done_since(since),
            },
            'user_productivity': user_productivity,
        }

    def user_report(self, user_id):
        user = User.find(user_id)
        if user is None:
            raise NotFoundError('Usuário não encontrado')

        tasks = Task.list_by_user(user_id)
        now = utcnow()
        counts = {status: 0 for status in (STATUS_DONE, STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_CANCELLED)}
        for task in tasks:
            if task.status in counts:
                counts[task.status] += 1
        total = len(tasks)

        return {
            'user': {'id': user.id, 'name': user.name, 'email': user.email},
            'statistics': {
                'total_tasks': total,
                'done': counts[STATUS_DONE],
                'pending': counts[STATUS_PENDING],
                'in_progress': counts[STATUS_IN_PROGRESS],
                'cancelled': counts[STATUS_CANCELLED],
                'overdue': sum(1 for task in tasks if task.is_overdue(now)),
                'high_priority': sum(1 for task in tasks if task.priority <= HIGH_PRIORITY_THRESHOLD),
                'completion_rate': completion_rate(counts[STATUS_DONE], total),
            },
        }
