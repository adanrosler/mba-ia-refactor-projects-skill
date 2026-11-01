import logging

from errors import ValidationError

logger = logging.getLogger(__name__)


class AdminController:
    def __init__(self, admin):
        self.admin = admin

    def resetar_banco(self):
        self.admin.resetar()
        logger.warning("!!! BANCO DE DADOS RESETADO !!!")

    def executar_query(self, dados):
        sql = dados.get("sql", "") if isinstance(dados, dict) else ""
        if not sql or not isinstance(sql, str):
            raise ValidationError("Query não informada")
        logger.warning("Executando query administrativa")
        return self.admin.executar_sql(sql)
