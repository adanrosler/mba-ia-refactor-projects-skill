import logging

from sqlalchemy.exc import SQLAlchemyError

from database import db
from utils.errors import PersistenceError

logger = logging.getLogger(__name__)


def commit(error_message):
    """Confirma a unidade de trabalho atual; em falha faz rollback e lança PersistenceError."""
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception(error_message)
        raise PersistenceError(error_message)


def paginate(query, page=None, per_page=None):
    """Aplica LIMIT/OFFSET apenas quando a paginação foi pedida; senão devolve tudo."""
    if page is None:
        return query.all()
    return query.limit(per_page).offset((page - 1) * per_page).all()
