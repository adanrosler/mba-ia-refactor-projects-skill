import re

from models.user import MIN_PASSWORD_LENGTH, ROLE_USER, VALID_ROLES
from utils.errors import ValidationError
from validators.common import require_payload

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')


def _email(value):
    if not isinstance(value, str) or not EMAIL_PATTERN.match(value):
        raise ValidationError('Email inválido')
    return value


def _password(value, too_short_message):
    if not isinstance(value, str):
        raise ValidationError('Senha inválida')
    if len(value) < MIN_PASSWORD_LENGTH:
        raise ValidationError(too_short_message)
    return value


def _name(value):
    if not value:
        raise ValidationError('Nome é obrigatório')
    if not isinstance(value, str):
        raise ValidationError('Nome inválido')
    return value


def validate_role(value):
    if value not in VALID_ROLES:
        raise ValidationError('Role inválido')
    return value


def validate_user_create(data):
    """Valida nome/email/senha; o role é validado depois da checagem de email duplicado."""
    require_payload(data)
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    if not name:
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password:
        raise ValidationError('Senha é obrigatória')
    return {
        'name': _name(name),
        'email': _email(email),
        'password': _password(password, f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres'),
        'role': data.get('role', ROLE_USER),
    }


def validate_user_update(data):
    require_payload(data)
    changes = {}
    if 'name' in data:
        changes['name'] = _name(data['name'])
    if 'email' in data:
        changes['email'] = _email(data['email'])
    if 'password' in data:
        changes['password'] = _password(data['password'], 'Senha muito curta')
    if 'role' in data:
        changes['role'] = validate_role(data['role'])
    if 'active' in data:
        if not isinstance(data['active'], bool):
            raise ValidationError('Campo active inválido')
        changes['active'] = data['active']
    return changes


def validate_login(data):
    require_payload(data)
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        raise ValidationError('Email e senha são obrigatórios')
    if not isinstance(email, str) or not isinstance(password, str):
        raise ValidationError('Credenciais inválidas', status=401)
    return email, password
