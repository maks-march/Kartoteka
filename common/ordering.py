"""Безопасная серверная сортировка для списков.

Любая сортировка данных выполняется на стороне БД (ORDER BY), а не на клиенте.
Чтобы не допустить произвольный order_by из пользовательского ввода, каждый
репозиторий передаёт белый список разрешённых полей (allowed) и поле/поля по
умолчанию (default).

Поддерживается последовательная (многоуровневая) сортировка: ``ordering``
может быть строкой ("name"), либо списком строк (["-status", "name"]) — поля
применяются в указанном порядке.
"""


def _normalize(ordering):
    """Приводит ordering к списку строк (терпит None / строку / список)."""
    if ordering is None:
        return []
    if isinstance(ordering, (list, tuple)):
        return [str(x) for x in ordering]
    return [str(ordering)]


def sanitize_ordering(ordering, allowed):
    """Возвращает список валидных полей сортировки (с префиксом '-' для убыв.).

    Недопустимые и повторяющиеся (по имени поля) значения отбрасываются —
    защита от инъекции произвольных полей в order_by.
    """
    result = []
    seen = set()
    for raw in _normalize(ordering):
        field = raw.strip()
        if not field:
            continue
        descending = field.startswith("-")
        bare = field[1:] if descending else field
        if bare in allowed and bare not in seen:
            seen.add(bare)
            result.append(("-" if descending else "") + bare)
    return result


def apply_ordering(qs, ordering, allowed, default=None):
    """Применяет ORDER BY к queryset.

    ordering — строка или список строк (поля, опционально с префиксом '-').
    allowed  — множество разрешённых имён полей (без префикса).
    default  — сортировка по умолчанию, если валидных полей нет.
    """
    fields = sanitize_ordering(ordering, allowed)
    if fields:
        return qs.order_by(*fields)

    if default is None:
        return qs
    if isinstance(default, (list, tuple)):
        return qs.order_by(*default)
    return qs.order_by(default)
