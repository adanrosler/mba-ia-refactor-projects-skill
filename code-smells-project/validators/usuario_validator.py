from errors import ValidationError
from validators.common import exigir_objeto


def _texto(dados, campo):
    valor = dados.get(campo, "")
    return valor if isinstance(valor, str) else ""


def validar_usuario(dados):
    exigir_objeto(dados)
    nome, email, senha = _texto(dados, "nome"), _texto(dados, "email"), _texto(dados, "senha")
    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")
    return {"nome": nome, "email": email, "senha": senha}


def validar_login(dados):
    dados = dados if isinstance(dados, dict) else {}
    email, senha = _texto(dados, "email"), _texto(dados, "senha")
    if not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")
    return email, senha
