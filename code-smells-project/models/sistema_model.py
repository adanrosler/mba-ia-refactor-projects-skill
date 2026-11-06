"""Operações de sistema: health check e ferramentas administrativas."""
from models.database import get_db

TABELAS_RESET = ("itens_pedido", "pedidos", "produtos", "usuarios")  # ordem: filhos antes dos pais


def contagens():
    db = get_db()
    db.execute("SELECT 1")
    row = db.execute(
        """
        SELECT (SELECT COUNT(*) FROM produtos) AS produtos,
               (SELECT COUNT(*) FROM usuarios) AS usuarios,
               (SELECT COUNT(*) FROM pedidos) AS pedidos
        """
    ).fetchone()
    return dict(row)


def resetar_banco():
    db = get_db()
    with db:
        for tabela in TABELAS_RESET:
            db.execute(f"DELETE FROM {tabela}")  # nomes vindos de whitelist fixa


def executar_sql(sql):
    """Executa SQL administrativo. Só é alcançável com ENABLE_ADMIN_ENDPOINTS + ADMIN_TOKEN."""
    db = get_db()
    with db:
        cursor = db.execute(sql)
        if sql.strip().upper().startswith("SELECT"):
            return [dict(row) for row in cursor.fetchall()]
    return None
