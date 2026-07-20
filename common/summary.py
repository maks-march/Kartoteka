"""Помощники для сводных панелей в детальных карточках.

Сводка агрегирует данные из таблиц, расположенных ниже на странице
(системы/объекты/участники), в компактный набор уникальных сущностей.
"""

# Лимит по умолчанию отключён: показываем все элементы группы, а панель
# сводки прокручивается (см. .summary-panel .summary-body в style.css).
SUMMARY_LIMIT = None


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
    """Готовит группу для сводки: уникальные элементы.

    Возвращает dict: {"items": [...], "total": N, "more": ...}.
    По умолчанию (limit=None) показываем все элементы (more=0); панель
    сводки прокручивается. Если limit задан — обрезаем и считаем «ещё N».
    """
    uniq = unique_by(items, key)
    total = len(uniq)
    if limit is None:
        return {"items": uniq, "total": total, "more": 0}
    shown = uniq[:limit]
    return {"items": shown, "total": total, "more": max(0, total - limit)}
