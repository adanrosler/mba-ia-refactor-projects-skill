from database import db
from models.base import CrudMixin, paginate
from utils.time import utcnow

DEFAULT_COLOR = '#000000'


class Category(CrudMixin, db.Model):
    # Ao apagar uma categoria, o ORM anula tasks.category_id (relação Category.tasks)
    # na mesma transação, evitando referências órfãs.
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
    def list_all(cls, page=None, per_page=None):
        return paginate(cls.query.order_by(cls.id), page, per_page).all()
