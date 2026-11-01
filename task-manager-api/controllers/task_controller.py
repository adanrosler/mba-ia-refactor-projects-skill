import logging

from models.category import Category
from models.task import STATUS_DONE, Task
from models.user import User
from utils.errors import NotFoundError
from utils.numbers import percentage
from utils.time import utcnow
from validators.task_validator import (
    CREATE_DATE_ERROR, UPDATE_DATE_ERROR, parse_due_date, validate_search_filters,
    validate_task_create, validate_task_update,
)

logger = logging.getLogger(__name__)

TASK_NOT_FOUND = 'Task não encontrada'


def ensure_user_exists(user_id):
    if user_id and not User.get(user_id):
        raise NotFoundError('Usuário não encontrado')


def ensure_category_exists(category_id):
    if category_id and not Category.get(category_id):
        raise NotFoundError('Categoria não encontrada')


class TaskController:
    def __init__(self, notifier):
        self.notifier = notifier

    def _get_or_404(self, task_id):
        task = Task.get(task_id)
        if not task:
            raise NotFoundError(TASK_NOT_FOUND)
        return task

    def _notify_assignment(self, task):
        if task.user:
            self.notifier.notify_task_assigned(task.user, task)

    def list_tasks(self, page=None, per_page=None):
        tasks = Task.list_all(page, per_page, with_relations=True)
        return [task.to_dict(with_overdue=True, with_names=True) for task in tasks]

    def get_task(self, task_id):
        return self._get_or_404(task_id).to_dict(with_overdue=True)

    def create_task(self, data):
        fields = validate_task_create(data)
        ensure_user_exists(fields['user_id'])
        ensure_category_exists(fields['category_id'])

        task = Task(
            title=fields['title'],
            description=fields['description'],
            status=fields['status'],
            priority=fields['priority'],
            user_id=fields['user_id'],
            category_id=fields['category_id'],
        )
        if fields['due_date']:
            task.due_date = parse_due_date(fields['due_date'], CREATE_DATE_ERROR)
        if fields['tags']:
            task.set_tags(fields['tags'])

        task.save('Erro ao criar task')
        logger.info('Task criada: id=%s', task.id)
        self._notify_assignment(task)
        return task.to_dict()

    def update_task(self, task_id, data):
        task = self._get_or_404(task_id)
        changes = validate_task_update(data)
        if 'user_id' in changes:
            ensure_user_exists(changes['user_id'])
        if 'category_id' in changes:
            ensure_category_exists(changes['category_id'])
        if changes.get('due_date'):
            changes['due_date'] = parse_due_date(changes['due_date'], UPDATE_DATE_ERROR)
        elif 'due_date' in changes:
            changes['due_date'] = None

        reassigned = 'user_id' in changes and changes['user_id'] != task.user_id
        for field in ('title', 'description', 'status', 'priority', 'user_id', 'category_id', 'due_date'):
            if field in changes:
                setattr(task, field, changes[field])
        if 'tags' in changes:
            task.set_tags(changes['tags'])
        task.updated_at = utcnow()

        task.save('Erro ao atualizar')
        logger.info('Task atualizada: id=%s', task.id)
        if reassigned:
            self._notify_assignment(task)
        return task.to_dict()

    def delete_task(self, task_id):
        task = self._get_or_404(task_id)
        task.delete('Erro ao deletar')
        logger.info('Task deletada: id=%s', task_id)
        return {'message': 'Task deletada com sucesso'}

    def search_tasks(self, text, status, priority, user_id, page=None, per_page=None):
        filters = validate_search_filters(text, status, priority, user_id)
        return [task.to_dict() for task in Task.search(**filters, page=page, per_page=per_page)]

    def stats(self):
        total = Task.count()
        by_status = Task.count_by_status()
        return {
            'total': total,
            **by_status,
            'overdue': Task.count_overdue(utcnow()),
            'completion_rate': percentage(by_status[STATUS_DONE], total),
        }
