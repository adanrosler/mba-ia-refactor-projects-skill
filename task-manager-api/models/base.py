import logging

from sqlalchemy.exc import SQLAlchemyError

from database import db
from utils.errors import PersistenceError

logger = logging.getLogger(__name__)


def commit(error_message):
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception(error_message)
        raise PersistenceError(error_message)


def paginate(query, page=None, per_page=None):
    if not page:
        return query
    return query.limit(per_page).offset((page - 1) * per_page)


class CrudMixin:
    @classmethod
    def get(cls, entity_id):
        return db.session.get(cls, entity_id)

    @classmethod
    def count(cls):
        return cls.query.count()

    def save(self, error_message='Erro ao salvar'):
        db.session.add(self)
        commit(error_message)
        return self

    def delete(self, error_message='Erro ao deletar'):
        db.session.delete(self)
        commit(error_message)
