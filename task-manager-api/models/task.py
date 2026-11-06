from sqlalchemy import case, func
from sqlalchemy.orm import joinedload

from database import db
from models.base import commit, paginate
from utils.constants import CLOSED_STATUSES, DEFAULT_PRIORITY, STATUS_DONE, STATUS_PENDING
from utils.time import utcnow


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=STATUS_PENDING)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    # ---- regras da entidade -------------------------------------------------
    def is_overdue(self, now=None):
        now = now or utcnow()
        return bool(self.due_date and self.due_date < now and self.status not in CLOSED_STATUSES)

    def days_overdue(self, now=None):
        return ((now or utcnow()) - self.due_date).days

    def set_tags(self, tags):
        self.tags = ','.join(tags) if isinstance(tags, list) else tags

    # ---- serialização -------------------------------------------------------
    def to_dict(self, with_overdue=False, with_names=False):
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'tags': self.tags.split(',') if self.tags else [],
        }
        if with_overdue:
            data['overdue'] = self.is_overdue()
        if with_names:
            data['user_name'] = self.user.name if self.user else None
            data['category_name'] = self.category.name if self.category else None
        return data

    def to_summary_dict(self):
        """Formato reduzido usado em /users/<id>/tasks."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'created_at': str(self.created_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'overdue': self.is_overdue(),
        }

    # ---- consultas ----------------------------------------------------------
    @classmethod
    def find(cls, task_id):
        return db.session.get(cls, task_id)

    @classmethod
    def list_with_relations(cls, page=None, per_page=None):
        query = cls.query.options(joinedload(cls.user), joinedload(cls.category)).order_by(cls.id)
        return paginate(query, page, per_page)

    @classmethod
    def list_all(cls):
        return cls.query.order_by(cls.id).all()

    @classmethod
    def list_by_user(cls, user_id):
        return cls.query.filter_by(user_id=user_id).order_by(cls.id).all()

    @classmethod
    def search(cls, text=None, status=None, priority=None, user_id=None):
        query = cls.query
        if text:
            pattern = f'%{text}%'
            query = query.filter(db.or_(cls.title.like(pattern), cls.description.like(pattern)))
        if status:
            query = query.filter(cls.status == status)
        if priority is not None:
            query = query.filter(cls.priority == priority)
        if user_id is not None:
            query = query.filter(cls.user_id == user_id)
        return query.order_by(cls.id).all()

    @classmethod
    def count(cls):
        return cls.query.count()

    @classmethod
    def count_by_status(cls):
        return dict(db.session.query(cls.status, func.count(cls.id)).group_by(cls.status).all())

    @classmethod
    def count_by_priority(cls):
        return dict(db.session.query(cls.priority, func.count(cls.id)).group_by(cls.priority).all())

    @classmethod
    def _overdue_filter(cls, query, now):
        return query.filter(cls.due_date.isnot(None), cls.due_date < now,
                            cls.status.notin_(CLOSED_STATUSES))

    @classmethod
    def list_overdue(cls, now=None):
        return cls._overdue_filter(cls.query, now or utcnow()).order_by(cls.id).all()

    @classmethod
    def count_overdue(cls, now=None):
        return cls._overdue_filter(cls.query, now or utcnow()).count()

    @classmethod
    def count_created_since(cls, since):
        return cls.query.filter(cls.created_at >= since).count()

    @classmethod
    def count_done_since(cls, since):
        return cls.query.filter(cls.status == STATUS_DONE, cls.updated_at >= since).count()

    @classmethod
    def totals_by_user(cls):
        """{user_id: (total, concluídas)} numa única query agregada."""
        done = func.sum(case((cls.status == STATUS_DONE, 1), else_=0))
        rows = db.session.query(cls.user_id, func.count(cls.id), done).group_by(cls.user_id).all()
        return {user_id: (total, int(completed or 0)) for user_id, total, completed in rows}

    # ---- persistência -------------------------------------------------------
    def save(self, error_message):
        db.session.add(self)
        commit(error_message)

    def delete(self, error_message):
        db.session.delete(self)
        commit(error_message)
