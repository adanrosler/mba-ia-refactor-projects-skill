import logging

from errors import NotFoundError, UnauthorizedError
from validators.usuario_validator import validar_login, validar_usuario

logger = logging.getLogger(__name__)


class UsuarioController:
    def __init__(self, usuarios):
        self.usuarios = usuarios

    def listar(self, limit=None, offset=0):
        return self.usuarios.listar(limit, offset)

    def obter(self, usuario_id):
        usuario = self.usuarios.buscar_por_id(usuario_id)
        if not usuario:
            raise NotFoundError("Usuário não encontrado")
        return usuario

    def criar(self, dados):
        usuario = validar_usuario(dados)
        usuario_id = self.usuarios.criar(**usuario)
        logger.info("Usuário criado: id=%s", usuario_id)
        return usuario_id

    def login(self, dados):
        email, senha = validar_login(dados)
        usuario = self.usuarios.autenticar(email, senha)
        if not usuario:
            logger.info("Login falhou")
            raise UnauthorizedError("Email ou senha inválidos", payload={"sucesso": False})
        logger.info("Login bem-sucedido: id=%s", usuario["id"])
        return usuario
