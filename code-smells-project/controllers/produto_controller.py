import logging

from errors import NotFoundError
from validators.produto_validator import validar_filtro_preco, validar_produto

logger = logging.getLogger(__name__)


class ProdutoController:
    def __init__(self, produtos):
        self.produtos = produtos

    def listar(self, limit=None, offset=0):
        produtos = self.produtos.listar(limit, offset)
        logger.info("Listando %d produtos", len(produtos))
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
        produto = validar_produto(dados)
        produto_id = self.produtos.criar(**produto)
        logger.info("Produto criado com ID: %s", produto_id)
        return produto_id

    def atualizar(self, produto_id, dados):
        self._garantir_existe(produto_id)
        produto = validar_produto(dados)
        self.produtos.atualizar(produto_id, **produto)

    def deletar(self, produto_id):
        self._garantir_existe(produto_id)
        self.produtos.deletar(produto_id)
        logger.info("Produto %s deletado", produto_id)

    def buscar(self, termo, categoria, preco_min, preco_max):
        return self.produtos.buscar(
            termo, categoria, validar_filtro_preco(preco_min), validar_filtro_preco(preco_max)
        )
