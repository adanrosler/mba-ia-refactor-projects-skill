import logging
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)

SMTP_TIMEOUT_SECONDS = 10


class NotificationService:
    """Envio de e-mails. Sem credenciais SMTP configuradas opera em modo desabilitado."""

    def __init__(self, host=None, port=587, user=None, password=None, smtp_factory=smtplib.SMTP):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self._smtp_factory = smtp_factory

    @property
    def enabled(self):
        return bool(self.host and self.user and self.password)

    def send_email(self, to, subject, body):
        if not self.enabled:
            logger.debug('SMTP não configurado; e-mail não enviado: %s', subject)
            return False

        message = EmailMessage()
        message['From'] = self.user
        message['To'] = to
        message['Subject'] = subject
        message.set_content(body)
        try:
            with self._smtp_factory(self.host, self.port, timeout=SMTP_TIMEOUT_SECONDS) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.send_message(message)
        except (smtplib.SMTPException, OSError):
            logger.exception('Erro ao enviar e-mail: %s', subject)
            return False
        logger.info('E-mail enviado: %s', subject)
        return True

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
            f"Prioridade: {task.priority}\nStatus: {task.status}"
        )
        return self.send_email(user.email, subject, body)

    def notify_task_overdue(self, user, task):
        subject = f"Task atrasada: {task.title}"
        body = f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\nData limite: {task.due_date}"
        return self.send_email(user.email, subject, body)
