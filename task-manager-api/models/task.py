from sqlalchemy import case, func
from sqlalchemy.orm import joinedload

from database import db
from models.base import CrudMixin, paginate
from utils.time import utcnow

STATUS_PENDING = 'pending'
STATUS_IN_PROGRESS = 'in_progress'
STATUS_DONE = 'done'
STATUS_CANCELLED = 'cancelled'
VALID_STATUSES = (STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED)
CLOSED_STATUSES = (STATUS_DONE, STATUS_CANCELLED)

MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_MAX = 2
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
TAG_SEPARATOR = ','


class Task(CrudMixin, db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(MAX_TITLE_LENGTH), nullable=False)
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

    def is_overdue(self, now=None):
        now = now or utcnow()
        return bool(self.due_date and self.due_date < now and self.status not in CLOSED_STATUSES)

    def set_tags(self, tags):
        self.tags = TAG_SEPARATOR.join(tags) if isinstance(tags, list) else tags

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
            'tags': self.tags.split(TAG_SEPARATOR) if self.tags else [],
        }
        if with_overdue:
            data['overdue'] = self.is_overdue()
        if with_names:
            data['user_name'] = self.user.name if self.user else None
            data['category_name'] = self.category.name if self.category else None
        return data

    def to_brief_dict(self):
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

    # ---- consultas -------------------------------------------------------

    @classmethod
    def list_all(cls, page=None, per_page=None, with_relations=False):
        query = cls.query.order_by(cls.id)
        if with_relations:
            query = query.options(joinedload(cls.user), joinedload(cls.category))
        return paginate(query, page, per_page).all()

    @classmethod
    def search(cls, text=None, status=None, priority=None, user_id=None, page=None, per_page=None):
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
        return paginate(query.order_by(cls.id), page, per_page).all()

    @classmethod
    def list_by_user(cls, user_id):
        return cls.query.filter_by(user_id=user_id).order_by(cls.id).all()

    @classmethod
    def _overdue_filter(cls, now):
        return (cls.due_date.isnot(None), cls.due_date < now, cls.status.notin_(CLOSED_STATUSES))

    @classmethod
    def list_overdue(cls, now):
        return cls.query.filter(*cls._overdue_filter(now)).order_by(cls.id).all()

    @classmethod
    def count_overdue(cls, now):
        return cls.query.filter(*cls._overdue_filter(now)).count()

    @classmethod
    def count_by(cls, column):
        rows = db.session.query(column, func.count(cls.id)).group_by(column).all()
        return {key: total for key, total in rows}

    @classmethod
    def count_by_status(cls):
        counts = cls.count_by(cls.status)
        return {status: counts.get(status, 0) for status in VALID_STATUSES}

    @classmethod
    def count_by_priority(cls):
        counts = cls.count_by(cls.priority)
        return {priority: counts.get(priority, 0) for priority in PRIORITY_LABELS}

    @classmethod
    def count_created_since(cls, since):
        return cls.query.filter(cls.created_at >= since).count()

    @classmethod
    def count_completed_since(cls, since):
        return cls.query.filter(cls.status == STATUS_DONE, cls.updated_at >= since).count()

    @classmethod
    def completion_by_user(cls):
        """{user_id: (total, concluídas)} em uma única consulta agregada."""
        done = func.sum(case((cls.status == STATUS_DONE, 1), else_=0))
        rows = db.session.query(cls.user_id, func.count(cls.id), done).group_by(cls.user_id).all()
        return {user_id: (total, completed or 0) for user_id, total, completed in rows}
