from errors import ValidationError
from models.pedido_model import STATUS_VALIDOS
from validators.common import is_int


def validar_pedido(dados):
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    if not isinstance(itens, list):
        raise ValidationError("Itens inválidos")
    for item in itens:
        if not isinstance(item, dict) or not is_int(item.get("produto_id")) or not is_int(item.get("quantidade")):
            raise ValidationError("Item inválido: produto_id e quantidade (inteiros) são obrigatórios")
        if item["quantidade"] <= 0:
            raise ValidationError("Quantidade deve ser maior que zero")
    return usuario_id, itens


def validar_status(dados):
    novo_status = dados.get("status", "") if isinstance(dados, dict) else ""
    if novo_status not in STATUS_VALIDOS:
        raise ValidationError("Status inválido")
    return novo_status
