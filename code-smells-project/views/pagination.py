from flask import request

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


def pagination_args():
    """(limit, offset) quando ?page= é informado; (None, 0) mantém a listagem completa original."""
    page = request.args.get("page", type=int)
    if not page or page < 1:
        return None, 0
    per_page = request.args.get("per_page", default=DEFAULT_PAGE_SIZE, type=int)
    per_page = max(1, min(per_page, MAX_PAGE_SIZE))
    return per_page, (page - 1) * per_page
