from models.relatorio_model import calcular_desconto


class RelatorioController:
    def __init__(self, relatorios):
        self.relatorios = relatorios

    def vendas(self):
        resumo = self.relatorios.resumo_vendas()
        total_pedidos = resumo["total_pedidos"]
        faturamento = resumo["faturamento"]
        desconto = calcular_desconto(faturamento)
        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, 2),
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento - desconto, 2),
            "pedidos_pendentes": resumo["pendentes"],
            "pedidos_aprovados": resumo["aprovados"],
            "pedidos_cancelados": resumo["cancelados"],
            "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
        }
