class AdminModel:
    """Operações administrativas (só acessíveis com ENABLE_ADMIN_ENDPOINTS habilitado)."""

    def __init__(self, get_connection):
        self._db = get_connection

    def resetar(self):
        conn = self._db()
        with conn:
            for tabela in ("itens_pedido", "pedidos", "produtos", "usuarios"):
                conn.execute(f"DELETE FROM {tabela}")  # nomes fixos (whitelist), sem entrada externa

    def executar_sql(self, sql):
        conn = self._db()
        if sql.strip().upper().startswith("SELECT"):
            return [dict(row) for row in conn.execute(sql).fetchall()]
        with conn:
            conn.execute(sql)
        return None
