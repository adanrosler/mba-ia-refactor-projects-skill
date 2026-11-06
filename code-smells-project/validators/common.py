from errors import ValidationError

MENSAGEM_DADOS_INVALIDOS = "Dados inválidos"


def exigir_objeto(dados, mensagem=MENSAGEM_DADOS_INVALIDOS):
    if not dados or not isinstance(dados, dict):
        raise ValidationError(mensagem)
    return dados


def is_numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def is_inteiro(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


def parse_float_opcional(valor, mensagem):
    if not valor:
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        raise ValidationError(mensagem)
