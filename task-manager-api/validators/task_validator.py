from datetime import datetime

from models.task import (
    DEFAULT_PRIORITY, MAX_PRIORITY, MAX_TITLE_LENGTH, MIN_PRIORITY, MIN_TITLE_LENGTH,
    STATUS_PENDING, VALID_STATUSES,
)
from utils.errors import ValidationError
from validators.common import optional_str, require_payload, to_int

DATE_FORMAT = '%Y-%m-%d'
CREATE_DATE_ERROR = 'Formato de data inválido. Use YYYY-MM-DD'
UPDATE_DATE_ERROR = 'Formato de data inválido'


def _title(value):
    if not isinstance(value, str):
        raise ValidationError('Título inválido')
    if len(value) < MIN_TITLE_LENGTH:
        raise ValidationError('Título muito curto')
    if len(value) > MAX_TITLE_LENGTH:
        raise ValidationError('Título muito longo')
    return value


def _status(value):
    if value not in VALID_STATUSES:
        raise ValidationError('Status inválido')
    return value


def _priority(value):
    if isinstance(value, float):
        raise ValidationError('Prioridade inválida')
    priority = to_int(value, 'Prioridade inválida')
    if not MIN_PRIORITY <= priority <= MAX_PRIORITY:
        raise ValidationError(f'Prioridade deve ser entre {MIN_PRIORITY} e {MAX_PRIORITY}')
    return priority


def _tags(value):
    if isinstance(value, list):
        if not all(isinstance(tag, str) for tag in value):
            raise ValidationError('Tags inválidas')
        return value
    if value is not None and not isinstance(value, str):
        raise ValidationError('Tags inválidas')
    return value


def parse_due_date(value, message):
    if not isinstance(value, str):
        raise ValidationError(message)
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except ValueError:
        raise ValidationError(message)


def validate_task_create(data):
    """Valida os campos simples; existência de usuário/categoria e data ficam no controller."""
    require_payload(data)
    title = data.get('title')
    if not title:
        raise ValidationError('Título é obrigatório')
    tags = data.get('tags')
    return {
        'title': _title(title),
        'description': optional_str(data.get('description', ''), 'Descrição inválida'),
        'status': _status(data.get('status', STATUS_PENDING)),
        'priority': _priority(data.get('priority', DEFAULT_PRIORITY)),
        'user_id': data.get('user_id'),
        'category_id': data.get('category_id'),
        'due_date': data.get('due_date'),
        'tags': _tags(tags) if tags else None,
    }


def validate_task_update(data):
    require_payload(data)
    changes = {}
    if 'title' in data:
        changes['title'] = _title(data['title'])
    if 'description' in data:
        changes['description'] = optional_str(data['description'], 'Descrição inválida')
    if 'status' in data:
        changes['status'] = _status(data['status'])
    if 'priority' in data:
        changes['priority'] = _priority(data['priority'])
    for key in ('user_id', 'category_id', 'due_date'):
        if key in data:
            changes[key] = data[key]
    if 'tags' in data:
        changes['tags'] = _tags(data['tags'])
    return changes


def validate_search_filters(text, status, priority, user_id):
    return {
        'text': text or None,
        'status': status or None,
        'priority': to_int(priority, 'Prioridade inválida') if priority else None,
        'user_id': to_int(user_id, 'Usuário inválido') if user_id else None,
    }
