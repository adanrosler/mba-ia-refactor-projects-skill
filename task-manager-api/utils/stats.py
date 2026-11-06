def completion_rate(done, total):
    """Percentual de conclusão com 2 casas; 0 quando não há tasks (mesmo formato do original)."""
    if total <= 0:
        return 0
    return round((done / total) * 100, 2)
