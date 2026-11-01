from datetime import timedelta

from models.category import Category
from models.task import (
    HIGH_PRIORITY_MAX, PRIORITY_LABELS, STATUS_CANCELLED, STATUS_DONE, STATUS_IN_PROGRESS,
    STATUS_PENDING, Task,
)
from models.user import User
from utils.errors import NotFoundError
from utils.numbers import percentage
from utils.time import utcnow

RECENT_ACTIVITY_DAYS = 7  # as chaves de recent_activity fazem parte do contrato da API


class ReportController:
    def summary(self):
        now = utcnow()
        since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
        by_priority = Task.count_by_priority()
        overdue_tasks = Task.list_overdue(now)
        completion = Task.completion_by_user()

        user_productivity = []
        for user in User.list_all():
            total, completed = completion.get(user.id, (0, 0))
            user_productivity.append({
                'user_id': user.id,
                'user_name': user.name,
                'total_tasks': total,
                'completed_tasks': completed,
                'completion_rate': percentage(completed, total),
            })

        return {
            'generated_at': str(now),
            'overview': {
                'total_tasks': Task.count(),
                'total_users': User.count(),
                'total_categories': Category.count(),
            },
            'tasks_by_status': Task.count_by_status(),
            'tasks_by_priority': {label: by_priority[level] for level, label in PRIORITY_LABELS.items()},
            'overdue': {
                'count': len(overdue_tasks),
                'tasks': [
                    {
                        'id': task.id,
                        'title': task.title,
                        'due_date': str(task.due_date),
                        'days_overdue': (now - task.due_date).days,
                    }
                    for task in overdue_tasks
                ],
            },
            'recent_activity': {
                'tasks_created_last_7_days': Task.count_created_since(since),
                'tasks_completed_last_7_days': Task.count_completed_since(since),
            },
            'user_productivity': user_productivity,
        }

    def user_report(self, user_id):
        user = User.get(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')

        tasks = Task.list_by_user(user_id)
        now = utcnow()
        by_status = {status: 0 for status in (STATUS_DONE, STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_CANCELLED)}
        for task in tasks:
            if task.status in by_status:
                by_status[task.status] += 1

        return {
            'user': user.to_contact_dict(),
            'statistics': {
                'total_tasks': len(tasks),
                **by_status,
                'overdue': sum(1 for task in tasks if task.is_overdue(now)),
                'high_priority': sum(1 for task in tasks if task.priority <= HIGH_PRIORITY_MAX),
                'completion_rate': percentage(by_status[STATUS_DONE], len(tasks)),
            },
        }
