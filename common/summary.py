"""Помощники для сводных панелей в детальных карточках.

Сводка агрегирует данные из таблиц, расположенных ниже на странице
(системы/объекты/участники), в компактный набор уникальных сущностей.
"""

# Максимум элементов в одной группе тегов сводки. Если больше — показываем
# первые SUMMARY_LIMIT и приписку «ещё N».
SUMMARY_LIMIT = 5


def unique_by(items, key):
    """Возвращает список уникальных элементов, сохраняя порядок первого вхождения.

    key(item) -> хэшируемый идентификатор (обычно pk).
    """
    seen = set()
    result = []
    for item in items:
        k = key(item)
        if k in seen:
            continue
        seen.add(k)
        result.append(item)
    return result


def summary_group(items, key, limit=SUMMARY_LIMIT):
    """Готовит группу для сводки: уникальные элементы, обрезанные до limit.

    Возвращает dict: {"items": [...до limit...], "total": N, "more": max(0, N-limit)}.
    Это сводка — лишние элементы не выводим, показываем «ещё N».
    """
    uniq = unique_by(items, key)
    total = len(uniq)
    shown = uniq[:limit]
    return {"items": shown, "total": total, "more": max(0, total - limit)}
