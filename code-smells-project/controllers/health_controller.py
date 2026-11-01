import logging
import sqlite3

logger = logging.getLogger(__name__)


class HealthController:
    def __init__(self, produtos, usuarios, pedidos, settings):
        self.produtos = produtos
        self.usuarios = usuarios
        self.pedidos = pedidos
        self.settings = settings

    def status(self):
        """Retorna (corpo, saudável?) — sem segredos nem configuração interna."""
        try:
            counts = {
                "produtos": self.produtos.contar(),
                "usuarios": self.usuarios.contar(),
                "pedidos": self.pedidos.contar(),
            }
        except sqlite3.Error:
            logger.exception("Health check falhou")
            return {"status": "erro", "detalhes": "Banco de dados indisponível"}, False
        return {
            "status": "ok",
            "database": "connected",
            "counts": counts,
            "versao": self.settings["APP_VERSION"],
            "ambiente": self.settings["APP_ENV"],
            "debug": self.settings["DEBUG"],
        }, True
