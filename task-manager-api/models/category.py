from sqlalchemy import func

from database import db
from models.base import commit, paginate
from utils.constants import DEFAULT_COLOR
from utils.time import utcnow


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default=DEFAULT_COLOR)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'created_at': str(self.created_at),
        }

    @classmethod
    def find(cls, category_id):
        return db.session.get(cls, category_id)

    @classmethod
    def list(cls, page=None, per_page=None):
        return paginate(cls.query.order_by(cls.id), page, per_page)

    @classmethod
    def count(cls):
        return cls.query.count()

    @staticmethod
    def task_counts():
        """{category_id: quantidade de tasks} numa única query agregada."""
        from models.task import Task
        rows = db.session.query(Task.category_id, func.count(Task.id)).group_by(Task.category_id).all()
        return dict(rows)

    def save(self, error_message):
        db.session.add(self)
        commit(error_message)

    def delete(self, error_message):
        """Remove a categoria desassociando as tasks na mesma transação (sem FKs órfãs)."""
        from models.task import Task
        Task.query.filter_by(category_id=self.id).update({Task.category_id: None})
        db.session.delete(self)
        commit(error_message)
