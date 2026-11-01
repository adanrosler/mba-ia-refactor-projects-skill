from models.database import paginate

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
CATEGORIA_PADRAO = "geral"
NOME_MIN_LEN = 2
NOME_MAX_LEN = 200

_COLUNAS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")


def to_dict(row):
    return {coluna: row[coluna] for coluna in _COLUNAS}


class ProdutoModel:
    def __init__(self, get_connection):
        self._db = get_connection

    def listar(self, limit=None, offset=0):
        clause, params = paginate(limit, offset)
        rows = self._db().execute("SELECT * FROM produtos ORDER BY id" + clause, params).fetchall()
        return [to_dict(row) for row in rows]

    def buscar_por_id(self, produto_id):
        row = self._db().execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        return to_dict(row) if row else None

    def buscar_por_ids(self, produto_ids):
        ids = list(set(produto_ids))
        placeholders = ", ".join("?" for _ in ids)
        rows = self._db().execute(
            f"SELECT * FROM produtos WHERE id IN ({placeholders})", ids
        ).fetchall()
        return {row["id"]: to_dict(row) for row in rows}

    def criar(self, nome, descricao, preco, estoque, categoria):
        conn = self._db()
        with conn:
            cursor = conn.execute(
                "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                (nome, descricao, preco, estoque, categoria),
            )
        return cursor.lastrowid

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        conn = self._db()
        with conn:
            conn.execute(
                "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
                (nome, descricao, preco, estoque, categoria, produto_id),
            )

    def deletar(self, produto_id):
        # Itens de pedidos antigos mantêm o produto_id; a listagem de pedidos usa LEFT JOIN
        # e exibe "Desconhecido" (histórico de pedidos preservado).
        conn = self._db()
        with conn:
            conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))

    def buscar(self, termo, categoria=None, preco_min=None, preco_max=None):
        query, params = "SELECT * FROM produtos WHERE 1=1", []
        if termo:
            query += " AND (nome LIKE ? OR descricao LIKE ?)"
            params += [f"%{termo}%", f"%{termo}%"]
        if categoria:
            query += " AND categoria = ?"
            params.append(categoria)
        if preco_min:
            query += " AND preco >= ?"
            params.append(preco_min)
        if preco_max:
            query += " AND preco <= ?"
            params.append(preco_max)
        rows = self._db().execute(query + " ORDER BY id", params).fetchall()
        return [to_dict(row) for row in rows]

    def contar(self):
        return self._db().execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
