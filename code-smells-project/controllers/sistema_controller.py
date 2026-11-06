import logging

from errors import ForbiddenError, ValidationError

logger = logging.getLogger(__name__)


class SistemaController:
    def __init__(self, sistema, versao, ambiente, debug, admin_habilitado):
        self.sistema = sistema
        self.versao = versao
        self.ambiente = ambiente
        self.debug = debug
        self.admin_habilitado = admin_habilitado

    def health(self):
        """Retorna (corpo, status). Não expõe configuração interna nem detalhes de erro."""
        try:
            counts = self.sistema.contagens()
        except Exception:
            logger.exception("Health check falhou")
            return {"status": "erro", "detalhes": "Banco de dados indisponível"}, 500
        return {
            "status": "ok",
            "database": "connected",
            "counts": counts,
            "versao": self.versao,
            "ambiente": self.ambiente,
            "debug": self.debug,
        }, 200

    def _exigir_admin_habilitado(self):
        if not self.admin_habilitado:
            raise ForbiddenError("Endpoint administrativo desabilitado")

    def resetar_banco(self):
        self._exigir_admin_habilitado()
        self.sistema.resetar_banco()
        logger.warning("Banco de dados resetado via /admin/reset-db")

    def executar_query(self, dados):
        self._exigir_admin_habilitado()
        sql = dados.get("sql", "") if isinstance(dados, dict) else ""
        if not sql or not isinstance(sql, str):
            raise ValidationError("Query não informada")
        logger.warning("Execução de SQL administrativo via /admin/query")
        return self.sistema.executar_sql(sql)
