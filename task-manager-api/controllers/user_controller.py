import logging

from models.task import Task
from models.user import ROLE_USER, User
from utils.errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from validators.user_validator import (
    validate_login, validate_role, validate_user_create, validate_user_update,
)

logger = logging.getLogger(__name__)

USER_NOT_FOUND = 'Usuário não encontrado'
EMAIL_TAKEN = 'Email já cadastrado'
INVALID_CREDENTIALS = 'Credenciais inválidas'
PERMISSION_DENIED = 'Permissão negada'


class UserController:
    def __init__(self, token_service, auth_required=False):
        self.token_service = token_service
        self.auth_required = auth_required

    def _get_or_404(self, user_id):
        user = User.get(user_id)
        if not user:
            raise NotFoundError(USER_NOT_FOUND)
        return user

    def _is_admin(self, actor):
        return actor is not None and actor.is_admin()

    def list_users(self, page=None, per_page=None):
        task_counts = Task.count_by(Task.user_id)
        return [
            {**user.to_dict(), 'task_count': task_counts.get(user.id, 0)}
            for user in User.list_all(page, per_page)
        ]

    def get_user(self, user_id):
        user = self._get_or_404(user_id)
        data = user.to_dict()
        data['tasks'] = [task.to_dict() for task in Task.list_by_user(user_id)]
        return data

    def create_user(self, data, actor=None):
        fields = validate_user_create(data)
        if User.find_by_email(fields['email']):
            raise ConflictError(EMAIL_TAKEN)
        role = validate_role(fields['role'])
        if self.auth_required and role != ROLE_USER and not self._is_admin(actor):
            raise ForbiddenError(PERMISSION_DENIED)

        user = User(name=fields['name'], email=fields['email'], role=role)
        user.set_password(fields['password'])
        user.save('Erro ao criar usuário')
        logger.info('Usuário criado: id=%s', user.id)
        return user.to_dict()

    def update_user(self, user_id, data, actor=None):
        user = self._get_or_404(user_id)
        changes = validate_user_update(data)
        if self.auth_required and not self._is_admin(actor):
            if actor is None or actor.id != user.id or 'role' in changes or 'active' in changes:
                raise ForbiddenError(PERMISSION_DENIED)

        if 'email' in changes:
            existing = User.find_by_email(changes['email'])
            if existing and existing.id != user_id:
                raise ConflictError(EMAIL_TAKEN)
        for field in ('name', 'email', 'role', 'active'):
            if field in changes:
                setattr(user, field, changes[field])
        if 'password' in changes:
            user.set_password(changes['password'])

        user.save('Erro ao atualizar')
        return user.to_dict()

    def delete_user(self, user_id):
        user = self._get_or_404(user_id)
        user.delete_with_tasks()
        logger.info('Usuário deletado: id=%s', user_id)
        return {'message': 'Usuário deletado com sucesso'}

    def list_user_tasks(self, user_id):
        self._get_or_404(user_id)
        return [task.to_brief_dict() for task in Task.list_by_user(user_id)]

    def login(self, data):
        email, password = validate_login(data)
        user = User.find_by_email(email)
        if not user or not user.check_password(password):
            raise UnauthorizedError(INVALID_CREDENTIALS)
        if not user.active:
            raise ForbiddenError('Usuário inativo')
        return {
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': self.token_service.issue(user.id),
        }
