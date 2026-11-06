"""Notificações (simuladas via log). Substituível por integração real no composition root."""
import logging

from models.pedido_model import STATUS_APROVADO, STATUS_CANCELADO

logger = logging.getLogger(__name__)


class NotificationService:
    def pedido_criado(self, pedido_id, usuario_id):
        logger.info("Notificação [email]: pedido %s criado para usuario %s", pedido_id, usuario_id)
        logger.info("Notificação [sms]: pedido %s recebido", pedido_id)
        logger.info("Notificação [push]: novo pedido %s recebido pelo sistema", pedido_id)

    def status_alterado(self, pedido_id, novo_status):
        if novo_status == STATUS_APROVADO:
            logger.info("Notificação: pedido %s aprovado. Preparar envio.", pedido_id)
        elif novo_status == STATUS_CANCELADO:
            logger.info("Notificação: pedido %s cancelado. Devolver estoque.", pedido_id)
