"""Acesso a dados de produtos."""
from models.database import get_db

CATEGORIAS_VALIDAS = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")
CATEGORIA_PADRAO = "geral"


def to_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco": row["preco"],
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": row["ativo"],
        "criado_em": row["criado_em"],
    }


def listar(limit=None, offset=0):
    sql, params = "SELECT * FROM produtos ORDER BY id", []
    if limit is not None:
        sql += " LIMIT ? OFFSET ?"
        params += [limit, offset]
    return [to_dict(row) for row in get_db().execute(sql, params).fetchall()]


def buscar_por_id(produto_id):
    row = get_db().execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    return to_dict(row) if row else None


def buscar(termo, categoria=None, preco_min=None, preco_max=None):
    sql, params = "SELECT * FROM produtos WHERE 1=1", []
    if termo:
        sql += " AND (nome LIKE ? OR descricao LIKE ?)"
        params += [f"%{termo}%", f"%{termo}%"]
    if categoria:
        sql += " AND categoria = ?"
        params.append(categoria)
    if preco_min:
        sql += " AND preco >= ?"
        params.append(preco_min)
    if preco_max:
        sql += " AND preco <= ?"
        params.append(preco_max)
    sql += " ORDER BY id"
    return [to_dict(row) for row in get_db().execute(sql, params).fetchall()]


def criar(nome, descricao, preco, estoque, categoria):
    db = get_db()
    with db:
        cursor = db.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
    return cursor.lastrowid


def atualizar(produto_id, nome, descricao, preco, estoque, categoria):
    db = get_db()
    with db:
        db.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, produto_id),
        )


def deletar(produto_id):
    """Remove o produto. Os itens de pedidos já feitos são histórico e são preservados
    (guardam preco_unitario); a leitura dos pedidos mostra o nome como "Desconhecido"."""
    db = get_db()
    with db:
        db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
