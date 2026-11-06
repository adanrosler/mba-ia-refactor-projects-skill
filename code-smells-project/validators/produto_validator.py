from errors import ValidationError
from models.produto_model import CATEGORIA_PADRAO, CATEGORIAS_VALIDAS
from validators.common import exigir_objeto, is_inteiro, is_numero

NOME_MIN = 2
NOME_MAX = 200


def validar_produto(dados):
    """Regras únicas para criação e atualização. Retorna os campos normalizados."""
    exigir_objeto(dados)
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
    if not is_numero(preco):
        raise ValidationError("Preço inválido")
    if not is_inteiro(estoque):
        raise ValidationError("Estoque inválido")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < NOME_MIN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_MAX:
        raise ValidationError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(list(CATEGORIAS_VALIDAS)))

    return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque, "categoria": categoria}
