import re

from models.category import DEFAULT_COLOR
from utils.errors import ValidationError
from validators.common import optional_str, require_payload

COLOR_PATTERN = re.compile(r'^#[0-9a-fA-F]{6}$')


def _color(value):
    if value is not None and (not isinstance(value, str) or not COLOR_PATTERN.match(value)):
        raise ValidationError('Cor inválida')
    return value


def _name(value):
    if not value:
        raise ValidationError('Nome é obrigatório')
    if not isinstance(value, str):
        raise ValidationError('Nome inválido')
    return value


def validate_category_create(data):
    require_payload(data)
    return {
        'name': _name(data.get('name')),
        'description': optional_str(data.get('description', ''), 'Descrição inválida'),
        'color': _color(data.get('color', DEFAULT_COLOR)),
    }


def validate_category_update(data):
    require_payload(data, allow_empty=True)
    changes = {}
    if 'name' in data:
        changes['name'] = _name(data['name'])
    if 'description' in data:
        changes['description'] = optional_str(data['description'], 'Descrição inválida')
    if 'color' in data:
        changes['color'] = _color(data['color'])
    return changes
