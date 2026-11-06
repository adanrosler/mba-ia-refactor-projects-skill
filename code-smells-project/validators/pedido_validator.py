from errors import ValidationError
from models.pedido_model import STATUS_VALIDOS
from validators.common import exigir_objeto, is_inteiro


def validar_pedido(dados):
    exigir_objeto(dados)
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not is_inteiro(usuario_id):
        raise ValidationError("Usuario ID inválido")
    if not itens or not isinstance(itens, list):
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    for item in itens:
        if (
            not isinstance(item, dict)
            or not is_inteiro(item.get("produto_id"))
            or not is_inteiro(item.get("quantidade"))
            or item["quantidade"] <= 0
        ):
            raise ValidationError("Item de pedido inválido")
    return usuario_id, itens


def validar_status(dados):
    novo_status = dados.get("status", "") if isinstance(dados, dict) else ""
    if novo_status not in STATUS_VALIDOS:
        raise ValidationError("Status inválido")
    return novo_status
