# Faixas de desconto sobre o faturamento: (limite exclusivo, taxa), em ordem decrescente.
FAIXAS_DESCONTO = ((10_000, 0.10), (5_000, 0.05), (1_000, 0.02))


def calcular_desconto(faturamento):
    return next((faturamento * taxa for limite, taxa in FAIXAS_DESCONTO if faturamento > limite), 0)


class RelatorioController:
    def __init__(self, relatorios):
        self.relatorios = relatorios

    def vendas(self):
        totais = self.relatorios.totais_vendas()
        total_pedidos = totais["total_pedidos"]
        faturamento = totais["faturamento"]
        desconto = calcular_desconto(faturamento)
        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, 2),
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento - desconto, 2),
            "pedidos_pendentes": totais["pendentes"],
            "pedidos_aprovados": totais["aprovados"],
            "pedidos_cancelados": totais["cancelados"],
            "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
        }
