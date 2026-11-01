import hashlib
import hmac

from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from models.base import CrudMixin, commit, paginate
from utils.time import utcnow

ROLE_USER = 'user'
ROLE_ADMIN = 'admin'
ROLE_MANAGER = 'manager'
VALID_ROLES = (ROLE_USER, ROLE_ADMIN, ROLE_MANAGER)
MIN_PASSWORD_LENGTH = 4

_MODERN_HASH_PREFIXES = ('scrypt:', 'pbkdf2:')


class User(CrudMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=ROLE_USER)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    def to_contact_dict(self):
        return {'id': self.id, 'name': self.name, 'email': self.email}

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        """Verifica a senha; hashes MD5 legados são aceitos e migrados para o hash atual."""
        if self.password and self.password.startswith(_MODERN_HASH_PREFIXES):
            return check_password_hash(self.password, raw_password)
        legacy_hash = hashlib.md5(raw_password.encode()).hexdigest()
        if self.password and hmac.compare_digest(self.password, legacy_hash):
            self.set_password(raw_password)
            commit('Erro ao atualizar')
            return True
        return False

    def is_admin(self):
        return self.role == ROLE_ADMIN

    def delete_with_tasks(self):
        for task in self.tasks:
            db.session.delete(task)
        db.session.delete(self)
        commit('Erro ao deletar')

    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    @classmethod
    def list_all(cls, page=None, per_page=None):
        return paginate(cls.query.order_by(cls.id), page, per_page).all()
