"""Acesso a dados de pedidos e itens de pedido."""
from errors import ValidationError
from models.database import get_db

STATUS_PENDENTE = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_CANCELADO = "cancelado"
STATUS_VALIDOS = (STATUS_PENDENTE, STATUS_APROVADO, "enviado", "entregue", STATUS_CANCELADO)
NOME_PRODUTO_DESCONHECIDO = "Desconhecido"


class EstoqueInsuficienteError(ValidationError):
    pass


def _erro_pedido(mensagem, erro_cls=ValidationError):
    return erro_cls(mensagem, payload={"sucesso": False})


def criar(usuario_id, itens):
    """Cria o pedido, os itens e baixa o estoque numa única transação."""
    db = get_db()
    with db:  # commit ao final; rollback automático se qualquer passo falhar
        precos = {}
        total = 0
        for item in itens:
            produto = db.execute(
                "SELECT nome, preco, estoque FROM produtos WHERE id = ?", (item["produto_id"],)
            ).fetchone()
            if produto is None:
                raise _erro_pedido(f"Produto {item['produto_id']} não encontrado")
            if produto["estoque"] < item["quantidade"]:
                raise _erro_pedido(f"Estoque insuficiente para {produto['nome']}", EstoqueInsuficienteError)
            precos[item["produto_id"]] = (produto["nome"], produto["preco"])
            total = total + produto["preco"] * item["quantidade"]

        pedido_id = db.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
            (usuario_id, STATUS_PENDENTE, total),
        ).lastrowid

        for item in itens:
            nome, preco = precos[item["produto_id"]]
            db.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                (pedido_id, item["produto_id"], item["quantidade"], preco),
            )
            baixa = db.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                (item["quantidade"], item["produto_id"], item["quantidade"]),
            )
            if baixa.rowcount == 0:  # concorrência ou item repetido além do estoque
                raise _erro_pedido(f"Estoque insuficiente para {nome}", EstoqueInsuficienteError)

    return {"pedido_id": pedido_id, "total": total}


def _montar_pedidos(pedido_rows):
    """Monta pedidos com itens usando uma única query de itens (sem N+1)."""
    pedidos = [
        {
            "id": row["id"],
            "usuario_id": row["usuario_id"],
            "status": row["status"],
            "total": row["total"],
            "criado_em": row["criado_em"],
            "itens": [],
        }
        for row in pedido_rows
    ]
    if not pedidos:
        return pedidos

    por_id = {pedido["id"]: pedido for pedido in pedidos}
    marcadores = ", ".join("?" for _ in por_id)
    itens = get_db().execute(
        f"""
        SELECT ip.pedido_id, ip.produto_id, ip.quantidade, ip.preco_unitario, p.nome AS produto_nome
        FROM itens_pedido ip
        LEFT JOIN produtos p ON p.id = ip.produto_id
        WHERE ip.pedido_id IN ({marcadores})
        ORDER BY ip.id
        """,
        list(por_id),
    ).fetchall()
    for item in itens:
        por_id[item["pedido_id"]]["itens"].append({
            "produto_id": item["produto_id"],
            "produto_nome": item["produto_nome"] if item["produto_nome"] is not None else NOME_PRODUTO_DESCONHECIDO,
            "quantidade": item["quantidade"],
            "preco_unitario": item["preco_unitario"],
        })
    return pedidos


def listar_por_usuario(usuario_id):
    rows = get_db().execute("SELECT * FROM pedidos WHERE usuario_id = ? ORDER BY id", (usuario_id,)).fetchall()
    return _montar_pedidos(rows)


def listar(limit=None, offset=0):
    sql, params = "SELECT * FROM pedidos ORDER BY id", []
    if limit is not None:
        sql += " LIMIT ? OFFSET ?"
        params += [limit, offset]
    return _montar_pedidos(get_db().execute(sql, params).fetchall())


def atualizar_status(pedido_id, novo_status):
    db = get_db()
    with db:
        db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
