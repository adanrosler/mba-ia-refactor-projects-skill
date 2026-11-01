from utils.errors import ValidationError

INVALID_PAYLOAD = 'Dados inválidos'


def require_payload(data, allow_empty=False):
    if not isinstance(data, dict) or (not data and not allow_empty):
        raise ValidationError(INVALID_PAYLOAD)
    return data


def to_int(value, message):
    if isinstance(value, bool):
        raise ValidationError(message)
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationError(message)


def optional_str(value, message):
    if value is not None and not isinstance(value, str):
        raise ValidationError(message)
    return value
