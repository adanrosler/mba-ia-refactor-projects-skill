from errors import ValidationError

DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100


def limites(page, per_page):
    """Converte page/per_page em (limit, offset). Sem `page` → sem paginação (contrato original)."""
    if page is None:
        return None, 0
    per_page = DEFAULT_PER_PAGE if per_page is None else per_page
    if page < 1 or per_page < 1:
        raise ValidationError("Parâmetros de paginação inválidos")
    per_page = min(per_page, MAX_PER_PAGE)
    return per_page, (page - 1) * per_page
