from datetime import datetime

from utils.constants import (DATE_FORMAT, DEFAULT_PRIORITY, PRIORITY_MAX, PRIORITY_MIN,
                             STATUS_PENDING, TASK_STATUSES, TITLE_MAX_LENGTH, TITLE_MIN_LENGTH)
from utils.errors import ValidationError
from validators.common import is_int, require_json_object


def _check_title(title):
    if not isinstance(title, str):
        raise ValidationError('Título inválido')
    if len(title) < TITLE_MIN_LENGTH:
        raise ValidationError('Título muito curto')
    if len(title) > TITLE_MAX_LENGTH:
        raise ValidationError('Título muito longo')
    return title


def _check_status(status):
    if status not in TASK_STATUSES:
        raise ValidationError('Status inválido')
    return status


def _check_priority(priority):
    if not is_int(priority):
        raise ValidationError('Prioridade inválida')
    if priority < PRIORITY_MIN or priority > PRIORITY_MAX:
        raise ValidationError(f'Prioridade deve ser entre {PRIORITY_MIN} e {PRIORITY_MAX}')
    return priority


def _check_reference(value, field):
    if value in (None, ''):
        return None
    if not is_int(value):
        raise ValidationError(f'{field} inválido')
    return value


def _parse_due_date(value, error_message):
    if not value:
        return None
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except (TypeError, ValueError):
        raise ValidationError(error_message)


def validate_task_create(data):
    data = require_json_object(data)
    title = data.get('title')
    if not title:
        raise ValidationError('Título é obrigatório')
    return {
        'title': _check_title(title),
        'description': data.get('description', ''),
        'status': _check_status(data.get('status', STATUS_PENDING)),
        'priority': _check_priority(data.get('priority', DEFAULT_PRIORITY)),
        'user_id': _check_reference(data.get('user_id'), 'user_id'),
        'category_id': _check_reference(data.get('category_id'), 'category_id'),
        'due_date': _parse_due_date(data.get('due_date'), 'Formato de data inválido. Use YYYY-MM-DD'),
        'tags': data.get('tags') or None,
    }


def validate_task_update(data):
    """Retorna apenas os campos presentes no corpo, já validados."""
    data = require_json_object(data)
    changes = {}
    if 'title' in data:
        changes['title'] = _check_title(data['title'])
    if 'description' in data:
        changes['description'] = data['description']
    if 'status' in data:
        changes['status'] = _check_status(data['status'])
    if 'priority' in data:
        changes['priority'] = _check_priority(data['priority'])
    if 'user_id' in data:
        changes['user_id'] = _check_reference(data['user_id'], 'user_id')
    if 'category_id' in data:
        changes['category_id'] = _check_reference(data['category_id'], 'category_id')
    if 'due_date' in data:
        changes['due_date'] = _parse_due_date(data['due_date'], 'Formato de data inválido')
    if 'tags' in data:
        changes['tags'] = data['tags']
    return changes
