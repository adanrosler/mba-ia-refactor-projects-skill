import hashlib
import hmac

from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from models.base import commit, paginate
from utils.constants import DEFAULT_ROLE, ROLE_ADMIN
from utils.time import utcnow

_MODERN_HASH_PREFIXES = ('pbkdf2:', 'scrypt:')


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        # Nunca serializar o hash de senha.
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def uses_legacy_hash(self):
        return not (self.password or '').startswith(_MODERN_HASH_PREFIXES)

    def check_password(self, raw_password):
        """Verifica a senha; aceita hashes MD5 legados (o controller migra no login)."""
        if not self.uses_legacy_hash():
            return check_password_hash(self.password, raw_password)
        legacy_hash = hashlib.md5(raw_password.encode()).hexdigest()
        return bool(self.password) and hmac.compare_digest(self.password, legacy_hash)

    def is_admin(self):
        return self.role == ROLE_ADMIN

    @classmethod
    def find(cls, user_id):
        return db.session.get(cls, user_id)

    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    @classmethod
    def list(cls, page=None, per_page=None):
        return paginate(cls.query.order_by(cls.id), page, per_page)

    @classmethod
    def count(cls):
        return cls.query.count()

    @staticmethod
    def task_counts():
        """{user_id: quantidade de tasks} numa única query agregada."""
        from models.task import Task
        rows = db.session.query(Task.user_id, func.count(Task.id)).group_by(Task.user_id).all()
        return dict(rows)

    def save(self, error_message):
        db.session.add(self)
        commit(error_message)

    def delete_with_tasks(self, error_message):
        """Remove o usuário e as tasks dele numa única transação."""
        for task in self.tasks:
            db.session.delete(task)
        db.session.delete(self)
        commit(error_message)
