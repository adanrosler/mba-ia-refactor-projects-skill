# (faturamento mínimo exclusivo, taxa de desconto) — ordem decrescente
FAIXAS_DESCONTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))


def calcular_desconto(faturamento):
    return next((faturamento * taxa for limite, taxa in FAIXAS_DESCONTO if faturamento > limite), 0)


class RelatorioModel:
    def __init__(self, get_connection):
        self._db = get_connection

    def resumo_vendas(self):
        row = self._db().execute(
            """
            SELECT COUNT(*) AS total_pedidos,
                   COALESCE(SUM(total), 0) AS faturamento,
                   COALESCE(SUM(CASE WHEN status = 'pendente' THEN 1 ELSE 0 END), 0) AS pendentes,
                   COALESCE(SUM(CASE WHEN status = 'aprovado' THEN 1 ELSE 0 END), 0) AS aprovados,
                   COALESCE(SUM(CASE WHEN status = 'cancelado' THEN 1 ELSE 0 END), 0) AS cancelados
            FROM pedidos
            """
        ).fetchone()
        return dict(row)
