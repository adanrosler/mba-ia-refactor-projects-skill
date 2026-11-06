import logging

from controllers.pagination import limites
from errors import NotFoundError
from validators.common import parse_float_opcional
from validators.produto_validator import validar_produto

logger = logging.getLogger(__name__)


class ProdutoController:
    def __init__(self, produtos):
        self.produtos = produtos

    def listar(self, page=None, per_page=None):
        limit, offset = limites(page, per_page)
        produtos = self.produtos.listar(limit, offset)
        logger.info("Listando %s produtos", len(produtos))
        return produtos

    def obter(self, produto_id):
        produto = self.produtos.buscar_por_id(produto_id)
        if not produto:
            raise NotFoundError("Produto não encontrado", payload={"sucesso": False})
        return produto

    def _garantir_existe(self, produto_id):
        if not self.produtos.buscar_por_id(produto_id):
            raise NotFoundError("Produto não encontrado")

    def criar(self, dados):
        campos = validar_produto(dados)
        produto_id = self.produtos.criar(**campos)
        logger.info("Produto criado: id=%s", produto_id)
        return {"id": produto_id}

    def atualizar(self, produto_id, dados):
        self._garantir_existe(produto_id)
        campos = validar_produto(dados)
        self.produtos.atualizar(produto_id, **campos)

    def deletar(self, produto_id):
        self._garantir_existe(produto_id)
        self.produtos.deletar(produto_id)
        logger.info("Produto deletado: id=%s", produto_id)

    def buscar(self, termo, categoria, preco_min, preco_max):
        preco_min = parse_float_opcional(preco_min, "Parâmetro preco_min inválido")
        preco_max = parse_float_opcional(preco_max, "Parâmetro preco_max inválido")
        return self.produtos.buscar(termo, categoria, preco_min, preco_max)
