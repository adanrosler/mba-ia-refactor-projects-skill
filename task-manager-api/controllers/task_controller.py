import logging

from models.category import Category
from models.task import Task
from models.user import User
from utils.constants import STATUS_CANCELLED, STATUS_DONE, STATUS_IN_PROGRESS, STATUS_PENDING
from utils.errors import NotFoundError
from utils.stats import completion_rate
from utils.time import utcnow
from validators.task_validator import validate_task_create, validate_task_update

logger = logging.getLogger(__name__)


class TaskController:
    def __init__(self, notifier):
        self.notifier = notifier

    @staticmethod
    def _get_or_404(task_id):
        task = Task.find(task_id)
        if task is None:
            raise NotFoundError('Task não encontrada')
        return task

    @staticmethod
    def _ensure_references(user_id, category_id):
        user = None
        if user_id:
            user = User.find(user_id)
            if user is None:
                raise NotFoundError('Usuário não encontrado')
        if category_id and Category.find(category_id) is None:
            raise NotFoundError('Categoria não encontrada')
        return user

    def list_tasks(self, page=None, per_page=None):
        tasks = Task.list_with_relations(page, per_page)
        return [task.to_dict(with_overdue=True, with_names=True) for task in tasks]

    def get_task(self, task_id):
        return self._get_or_404(task_id).to_dict(with_overdue=True)

    def create_task(self, payload):
        fields = validate_task_create(payload)
        assignee = self._ensure_references(fields['user_id'], fields['category_id'])

        task = Task(title=fields['title'], description=fields['description'], status=fields['status'],
                    priority=fields['priority'], user_id=fields['user_id'],
                    category_id=fields['category_id'], due_date=fields['due_date'])
        if fields['tags']:
            task.set_tags(fields['tags'])
        task.save('Erro ao criar task')
        logger.info('Task criada: %s - %s', task.id, task.title)

        if assignee is not None:
            self.notifier.notify_task_assigned(assignee, task)
        return task.to_dict()

    def update_task(self, task_id, payload):
        task = self._get_or_404(task_id)
        changes = validate_task_update(payload)
        assignee = self._ensure_references(changes.get('user_id'), changes.get('category_id'))
        previous_user_id = task.user_id

        for field in ('title', 'description', 'status', 'priority', 'user_id', 'category_id', 'due_date'):
            if field in changes:
                setattr(task, field, changes[field])
        if 'tags' in changes:
            task.set_tags(changes['tags'])
        task.updated_at = utcnow()
        task.save('Erro ao atualizar')
        logger.info('Task atualizada: %s', task.id)

        if assignee is not None and task.user_id != previous_user_id:
            self.notifier.notify_task_assigned(assignee, task)
        return task.to_dict()

    def delete_task(self, task_id):
        task = self._get_or_404(task_id)
        task.delete('Erro ao deletar')
        logger.info('Task deletada: %s', task_id)
        return {'message': 'Task deletada com sucesso'}

    def search_tasks(self, text, status, priority, user_id):
        return [task.to_dict() for task in Task.search(text, status, priority, user_id)]

    def stats(self):
        total = Task.count()
        by_status = Task.count_by_status()
        done = by_status.get(STATUS_DONE, 0)
        return {
            'total': total,
            'pending': by_status.get(STATUS_PENDING, 0),
            'in_progress': by_status.get(STATUS_IN_PROGRESS, 0),
            'done': done,
            'cancelled': by_status.get(STATUS_CANCELLED, 0),
            'overdue': Task.count_overdue(),
            'completion_rate': completion_rate(done, total),
        }
