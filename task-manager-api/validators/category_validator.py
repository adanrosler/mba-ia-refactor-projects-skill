from utils.constants import COLOR_LENGTH, DEFAULT_COLOR
from utils.errors import ValidationError
from validators.common import require_json_object


def _check_color(color):
    if not (isinstance(color, str) and len(color) == COLOR_LENGTH and color.startswith('#')):
        raise ValidationError('Cor inválida')
    return color


def validate_category_create(data):
    data = require_json_object(data)
    name = data.get('name')
    if not name:
        raise ValidationError('Nome é obrigatório')
    if not isinstance(name, str):
        raise ValidationError('Nome inválido')
    return {
        'name': name,
        'description': data.get('description', ''),
        'color': _check_color(data.get('color', DEFAULT_COLOR)),
    }


def validate_category_update(data):
    # O original aceitava corpo vazio ({}) como "sem alterações"; só o corpo ausente é inválido.
    if not isinstance(data, dict):
        raise ValidationError('Dados inválidos')
    changes = {}
    if 'name' in data:
        if not isinstance(data['name'], str) or not data['name']:
            raise ValidationError('Nome inválido')
        changes['name'] = data['name']
    if 'description' in data:
        changes['description'] = data['description']
    if 'color' in data:
        changes['color'] = _check_color(data['color'])
    return changes
