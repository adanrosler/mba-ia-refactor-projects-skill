from errors import ValidationError
from models.database import paginate

STATUS_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]
STATUS_INICIAL = "pendente"
PRODUTO_DESCONHECIDO = "Desconhecido"


def calcular_total(itens, produtos):
    total = 0
    for item in itens:
        total = total + (produtos[item["produto_id"]]["preco"] * item["quantidade"])
    return total


class PedidoModel:
    def __init__(self, get_connection):
        self._db = get_connection

    def criar(self, usuario_id, itens, produtos, total):
        """Grava pedido, itens e baixa de estoque numa única transação."""
        conn = self._db()
        with conn:  # commit no fim; rollback automático em qualquer exceção
            cursor = conn.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
                (usuario_id, STATUS_INICIAL, total),
            )
            pedido_id = cursor.lastrowid
            for item in itens:
                produto = produtos[item["produto_id"]]
                conn.execute(
                    "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                    (pedido_id, item["produto_id"], item["quantidade"], produto["preco"]),
                )
                baixa = conn.execute(
                    "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                    (item["quantidade"], item["produto_id"], item["quantidade"]),
                )
                if baixa.rowcount == 0:
                    raise ValidationError("Estoque insuficiente para " + produto["nome"],
                                          payload={"sucesso": False})
        return pedido_id

    def listar(self, usuario_id=None, limit=None, offset=0):
        query, params = "SELECT * FROM pedidos", []
        if usuario_id is not None:
            query += " WHERE usuario_id = ?"
            params.append(usuario_id)
        clause, page_params = paginate(limit, offset)
        conn = self._db()
        rows = conn.execute(query + " ORDER BY id" + clause, params + page_params).fetchall()
        pedidos = [
            {
                "id": row["id"],
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": [],
            }
            for row in rows
        ]
        if not pedidos:
            return pedidos

        por_id = {pedido["id"]: pedido for pedido in pedidos}
        placeholders = ", ".join("?" for _ in por_id)
        itens = conn.execute(
            f"""
            SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario, p.nome AS produto_nome
            FROM itens_pedido i
            LEFT JOIN produtos p ON p.id = i.produto_id
            WHERE i.pedido_id IN ({placeholders})
            ORDER BY i.id
            """,
            list(por_id),
        ).fetchall()
        for item in itens:
            por_id[item["pedido_id"]]["itens"].append({
                "produto_id": item["produto_id"],
                "produto_nome": item["produto_nome"] if item["produto_nome"] is not None else PRODUTO_DESCONHECIDO,
                "quantidade": item["quantidade"],
                "preco_unitario": item["preco_unitario"],
            })
        return pedidos

    def atualizar_status(self, pedido_id, novo_status):
        conn = self._db()
        with conn:
            conn.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))

    def contar(self):
        return self._db().execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
