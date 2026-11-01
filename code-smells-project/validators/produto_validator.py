from errors import ValidationError
from models.produto_model import CATEGORIA_PADRAO, CATEGORIAS_VALIDAS, NOME_MAX_LEN, NOME_MIN_LEN
from validators.common import is_int, is_number


def validar_produto(dados):
    """Mesmas regras (e mensagens) para criação e atualização de produto."""
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    if "nome" not in dados:
        raise ValidationError("Nome é obrigatório")
    if "preco" not in dados:
        raise ValidationError("Preço é obrigatório")
    if "estoque" not in dados:
        raise ValidationError("Estoque é obrigatório")

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if not isinstance(nome, str):
        raise ValidationError("Nome inválido")
    if not isinstance(descricao, str):
        raise ValidationError("Descrição inválida")
    if not is_number(preco):
        raise ValidationError("Preço inválido")
    if not is_int(estoque):
        raise ValidationError("Estoque inválido")

    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < NOME_MIN_LEN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_MAX_LEN:
        raise ValidationError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))

    return {"nome": nome, "descricao": descricao, "preco": preco,
            "estoque": estoque, "categoria": categoria}


def validar_filtro_preco(valor):
    if not valor:
        return None
    try:
        return float(valor)
    except ValueError:
        raise ValidationError("Filtro de preço inválido")
