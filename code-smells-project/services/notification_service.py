import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Notificações simuladas (e-mail/SMS/push) — ponto único para plugar integrações reais."""

    def pedido_criado(self, pedido_id, usuario_id):
        logger.info("ENVIANDO EMAIL: Pedido %s criado para usuario %s", pedido_id, usuario_id)
        logger.info("ENVIANDO SMS: Seu pedido foi recebido!")
        logger.info("ENVIANDO PUSH: Novo pedido recebido pelo sistema")

    def status_pedido_alterado(self, pedido_id, novo_status):
        if novo_status == "aprovado":
            logger.info("NOTIFICAÇÃO: Pedido %s foi aprovado! Preparar envio.", pedido_id)
        elif novo_status == "cancelado":
            logger.info("NOTIFICAÇÃO: Pedido %s cancelado. Devolver estoque.", pedido_id)
