"""Acesso a dados de usuários e verificação de senha."""
import hmac

from werkzeug.security import check_password_hash, generate_password_hash

from models.database import get_db

TIPO_PADRAO = "cliente"
_HASH_PREFIXES = ("scrypt:", "pbkdf2:")


def to_dict(row):
    """Serialização pública: nunca inclui a senha."""
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def to_login_dict(row):
    return {"id": row["id"], "nome": row["nome"], "email": row["email"], "tipo": row["tipo"]}


def listar(limit=None, offset=0):
    sql, params = "SELECT * FROM usuarios ORDER BY id", []
    if limit is not None:
        sql += " LIMIT ? OFFSET ?"
        params += [limit, offset]
    return [to_dict(row) for row in get_db().execute(sql, params).fetchall()]


def buscar_por_id(usuario_id):
    row = get_db().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return to_dict(row) if row else None


def criar(nome, email, senha, tipo=TIPO_PADRAO):
    db = get_db()
    with db:
        cursor = db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, generate_password_hash(senha), tipo),
        )
    return cursor.lastrowid


def _senha_confere(db, row, senha):
    armazenada = row["senha"] or ""
    if armazenada.startswith(_HASH_PREFIXES):
        return check_password_hash(armazenada, senha)
    # Senha legada em texto puro: verifica e migra para hash no primeiro login válido.
    if hmac.compare_digest(armazenada.encode(), senha.encode()):
        with db:
            db.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (generate_password_hash(senha), row["id"]))
        return True
    return False


def autenticar(email, senha):
    db = get_db()
    rows = db.execute("SELECT * FROM usuarios WHERE email = ? ORDER BY id", (email,)).fetchall()
    for row in rows:
        if _senha_confere(db, row, senha):
            return to_login_dict(row)
    return None
