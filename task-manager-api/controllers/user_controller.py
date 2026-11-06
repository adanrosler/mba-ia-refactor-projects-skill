import logging

from models.task import Task
from models.user import User
from utils.constants import DEFAULT_ROLE
from utils.errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from validators.user_validator import (check_role, validate_login, validate_user_create,
                                       validate_user_update)

logger = logging.getLogger(__name__)


class UserController:
    def __init__(self, token_service):
        self.token_service = token_service

    @staticmethod
    def _get_or_404(user_id):
        user = User.find(user_id)
        if user is None:
            raise NotFoundError('Usuário não encontrado')
        return user

    @staticmethod
    def _ensure_email_available(email, owner_id=None):
        existing = User.find_by_email(email)
        if existing is not None and existing.id != owner_id:
            raise ConflictError('Email já cadastrado')

    def list_users(self, page=None, per_page=None):
        task_counts = User.task_counts()
        return [
            {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role,
                'active': user.active,
                'created_at': str(user.created_at),
                'task_count': task_counts.get(user.id, 0),
            }
            for user in User.list(page, per_page)
        ]

    def get_user(self, user_id):
        user = self._get_or_404(user_id)
        data = user.to_dict()
        data['tasks'] = [task.to_dict() for task in Task.list_by_user(user_id)]
        return data

    def create_user(self, payload, actor):
        fields = validate_user_create(payload)
        role = fields['role']
        # Cadastro público só com o papel padrão; papéis acima exigem admin autenticado.
        if role != DEFAULT_ROLE:
            if actor is None:
                raise UnauthorizedError('Não autorizado')
            if not actor.is_admin():
                raise ForbiddenError('Permissão negada')
        self._ensure_email_available(fields['email'])
        check_role(role)

        user = User(name=fields['name'], email=fields['email'], role=role)
        user.set_password(fields['password'])
        user.save('Erro ao criar usuário')
        logger.info('Usuário criado: %s', user.id)
        return user.to_dict()

    def update_user(self, user_id, payload, actor):
        user = self._get_or_404(user_id)
        if not actor.is_admin() and actor.id != user.id:
            raise ForbiddenError('Permissão negada')
        changes = validate_user_update(payload)
        if ('role' in changes or 'active' in changes) and not actor.is_admin():
            raise ForbiddenError('Permissão negada')

        if 'email' in changes:
            self._ensure_email_available(changes['email'], owner_id=user.id)
        for field in ('name', 'email', 'role', 'active'):
            if field in changes:
                setattr(user, field, changes[field])
        if 'password' in changes:
            user.set_password(changes['password'])
        user.save('Erro ao atualizar')
        return user.to_dict()

    def delete_user(self, user_id):
        user = self._get_or_404(user_id)
        user.delete_with_tasks('Erro ao deletar')
        logger.info('Usuário deletado: %s', user_id)
        return {'message': 'Usuário deletado com sucesso'}

    def list_user_tasks(self, user_id):
        self._get_or_404(user_id)
        return [task.to_summary_dict() for task in Task.list_by_user(user_id)]

    def login(self, payload):
        email, password = validate_login(payload)
        user = User.find_by_email(email)
        if user is None or not user.check_password(password):
            raise UnauthorizedError('Credenciais inválidas')
        if not user.active:
            raise ForbiddenError('Usuário inativo')
        if user.uses_legacy_hash():
            user.set_password(password)  # migra MD5 legado para hash forte
            user.save('Erro ao realizar login')
        return {
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': self.token_service.issue(user.id),
        }
