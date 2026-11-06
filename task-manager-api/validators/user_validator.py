import re

from utils.constants import DEFAULT_ROLE, EMAIL_REGEX, MIN_PASSWORD_LENGTH, USER_ROLES
from utils.errors import UnauthorizedError, ValidationError
from validators.common import require_json_object


def _is_valid_email(email):
    return isinstance(email, str) and re.match(EMAIL_REGEX, email) is not None


def check_role(role):
    if role not in USER_ROLES:
        raise ValidationError('Role inválido')
    return role


def validate_user_create(data):
    data = require_json_object(data)
    name, email, password = data.get('name'), data.get('email'), data.get('password')
    if not name:
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password:
        raise ValidationError('Senha é obrigatória')
    if not isinstance(name, str):
        raise ValidationError('Nome inválido')
    if not _is_valid_email(email):
        raise ValidationError('Email inválido')
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres')
    # role é validado pelo controller depois da checagem de autorização/duplicidade
    return {'name': name, 'email': email, 'password': password, 'role': data.get('role', DEFAULT_ROLE)}


def validate_user_update(data):
    data = require_json_object(data)
    changes = {}
    if 'name' in data:
        if not isinstance(data['name'], str) or not data['name'].strip():
            raise ValidationError('Nome inválido')
        changes['name'] = data['name']
    if 'email' in data:
        if not _is_valid_email(data['email']):
            raise ValidationError('Email inválido')
        changes['email'] = data['email']
    if 'password' in data:
        if not isinstance(data['password'], str) or len(data['password']) < MIN_PASSWORD_LENGTH:
            raise ValidationError('Senha muito curta')
        changes['password'] = data['password']
    if 'role' in data:
        changes['role'] = check_role(data['role'])
    if 'active' in data:
        if not isinstance(data['active'], bool):
            raise ValidationError('Valor de active inválido')
        changes['active'] = data['active']
    return changes


def validate_login(data):
    data = require_json_object(data)
    email, password = data.get('email'), data.get('password')
    if not email or not password:
        raise ValidationError('Email e senha são obrigatórios')
    if not isinstance(email, str) or not isinstance(password, str):
        raise UnauthorizedError('Credenciais inválidas')
    return email, password
