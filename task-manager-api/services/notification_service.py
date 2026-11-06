import logging
import smtplib

logger = logging.getLogger(__name__)


class NotificationService:
    """Envia notificações por e-mail. Sem SMTP configurado, opera em modo desabilitado (só log)."""

    def __init__(self, host=None, port=587, user=None, password=None):
        self.host = host
        self.port = port
        self.user = user
        self.password = password

    @property
    def enabled(self):
        return bool(self.host and self.user and self.password)

    def send_email(self, to, subject, body):
        if not self.enabled:
            logger.info('Notificação desabilitada (SMTP não configurado): "%s" para %s', subject, to)
            return False
        try:
            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.user, to, f'Subject: {subject}\n\n{body}')
            logger.info('Email enviado para %s', to)
            return True
        except (smtplib.SMTPException, OSError):
            logger.exception('Erro ao enviar email para %s', to)
            return False

    def notify_task_assigned(self, user, task):
        subject = f'Nova task atribuída: {task.title}'
        body = (f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
                f'Prioridade: {task.priority}\nStatus: {task.status}')
        return self.send_email(user.email, subject, body)

    def notify_task_overdue(self, user, task):
        subject = f'Task atrasada: {task.title}'
        body = f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\nData limite: {task.due_date}"
        return self.send_email(user.email, subject, body)
