from flask import current_app, request


def pagination_args():
    """(page, per_page) a partir da query string; (None, None) mantém a listagem completa."""
    page = request.args.get('page', type=int)
    if not page or page < 1:
        return None, None
    per_page = request.args.get('per_page', default=current_app.config['DEFAULT_PAGE_SIZE'], type=int)
    return page, max(1, min(per_page, current_app.config['MAX_PAGE_SIZE']))
