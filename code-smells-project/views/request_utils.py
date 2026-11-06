from flask import request


def json_body():
    """Corpo JSON ou None (nunca lança por corpo ausente/malformado)."""
    return request.get_json(silent=True)


def paginacao():
    return request.args.get("page", type=int), request.args.get("per_page", type=int)
