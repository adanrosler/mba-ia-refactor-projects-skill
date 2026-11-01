from werkzeug.security import check_password_hash, generate_password_hash

from models.database import paginate

TIPO_PADRAO = "cliente"
_HASH_PREFIXES = ("pbkdf2:", "scrypt:")

_COLUNAS_PUBLICAS = ("id", "nome", "email", "tipo", "criado_em")


def hash_senha(senha):
    return generate_password_hash(senha)


def senha_tem_hash(valor):
    return bool(valor) and valor.startswith(_HASH_PREFIXES)


def to_dict(row, campos=_COLUNAS_PUBLICAS):
    return {campo: row[campo] for campo in campos}


def migrar_senhas_texto_puro(conn):
    """Converte senhas legadas em texto puro para hash (executado no boot)."""
    rows = conn.execute("SELECT id, senha FROM usuarios").fetchall()
    legadas = [(hash_senha(row["senha"]), row["id"]) for row in rows
               if row["senha"] and not senha_tem_hash(row["senha"])]
    if legadas:
        with conn:
            conn.executemany("UPDATE usuarios SET senha = ? WHERE id = ?", legadas)
    return len(legadas)


class UsuarioModel:
    def __init__(self, get_connection):
        self._db = get_connection

    def listar(self, limit=None, offset=0):
        clause, params = paginate(limit, offset)
        rows = self._db().execute("SELECT * FROM usuarios ORDER BY id" + clause, params).fetchall()
        return [to_dict(row) for row in rows]

    def buscar_por_id(self, usuario_id):
        row = self._db().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        return to_dict(row) if row else None

    def autenticar(self, email, senha):
        rows = self._db().execute(
            "SELECT * FROM usuarios WHERE email = ? ORDER BY id", (email,)
        ).fetchall()
        for row in rows:
            if senha_tem_hash(row["senha"]) and check_password_hash(row["senha"], senha):
                return to_dict(row, ("id", "nome", "email", "tipo"))
        return None

    def criar(self, nome, email, senha, tipo=TIPO_PADRAO):
        conn = self._db()
        with conn:
            cursor = conn.execute(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                (nome, email, hash_senha(senha), tipo),
            )
        return cursor.lastrowid

    def contar(self):
        return self._db().execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
