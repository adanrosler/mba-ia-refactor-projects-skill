from utils.errors import ValidationError


def require_json_object(data):
    if not data or not isinstance(data, dict):
        raise ValidationError('Dados inválidos')
    return data


def parse_optional_int(value, field):
    """Converte parâmetro de query string em int; vazio → None; inválido → 400."""
    if value in (None, ''):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationError(f'Parâmetro {field} inválido')


def parse_pagination(args):
    """`?page=&per_page=` opcionais. Sem `page`, a listagem continua completa."""
    page = parse_optional_int(args.get('page'), 'page')
    if page is None:
        return None, None
    per_page = parse_optional_int(args.get('per_page'), 'per_page') or 20
    if page < 1 or per_page < 1:
        raise ValidationError('Parâmetros de paginação inválidos')
    return page, per_page


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)
