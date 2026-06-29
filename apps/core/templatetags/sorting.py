"""Шаблонные теги для серверной сортировки кликом по заголовку таблицы.

Сортировка многоуровневая (последовательная): последний изменённый столбец
уходит в конец списка ключей. Цикл по клику на столбец:
    нет → по убыванию (-поле) → по возрастанию (поле) → удалить из сортировки.

Вся логика — на сервере: тег формирует ссылку (GET) с новым набором ordering,
сохраняя остальные параметры строки запроса. Никакой клиентской сортировки.
"""
from urllib.parse import urlencode

from django import template

register = template.Library()


def _current_ordering(context):
    """Текущий список ordering: сперва из контекста, иначе из GET."""
    ordering = context.get("ordering")
    if ordering:
        return [str(x) for x in ordering]
    request = context.get("request")
    if request is not None:
        return request.GET.getlist("ordering")
    return []


def _state_for(ordering, field):
    """Возвращает ('asc'|'desc'|None) для поля в текущем ordering."""
    for item in ordering:
        if item == field:
            return "asc"
        if item == "-" + field:
            return "desc"
    return None


def _next_ordering(ordering, field):
    """Новый список ordering после клика по столбцу field.

    Цикл: none -> '-field' (desc) -> 'field' (asc) -> убрать.
    Изменяемый столбец всегда перемещается в конец (последний приоритет).
    """
    # удаляем прежние записи этого поля
    rest = [i for i in ordering if i not in (field, "-" + field)]
    state = _state_for(ordering, field)
    if state is None:
        rest.append("-" + field)      # 1-й клик: по убыванию
    elif state == "desc":
        rest.append(field)            # 2-й клик: по возрастанию
    else:  # 'asc'
        pass                          # 3-й клик: убрать сортировку по столбцу
    return rest


@register.simple_tag(takes_context=True)
def sort_header(context, field, label):
    """Рендерит кликабельный заголовок столбца со ссылкой на новый ordering."""
    from django.utils.html import format_html

    request = context.get("request")
    ordering = _current_ordering(context)
    state = _state_for(ordering, field)
    new_ordering = _next_ordering(ordering, field)

    # Базовые GET-параметры без ordering (их добавим заново списком)
    params = []
    if request is not None:
        for key in request.GET:
            if key == "ordering":
                continue
            for value in request.GET.getlist(key):
                params.append((key, value))
    for item in new_ordering:
        params.append(("ordering", item))

    query = urlencode(params)
    url = "?" + query if query else "?"

    # Индикатор направления + позиция в многоуровневой сортировке
    arrow = ""
    if state == "desc":
        arrow = " ▼"
    elif state == "asc":
        arrow = " ▲"

    priority = ""
    if state is not None and len(ordering) > 1:
        # номер приоритета (1 = первый ключ сортировки)
        names = [i.lstrip("-") for i in ordering]
        if field in names:
            priority = format_html('<sup class="sort-prio">{}</sup>', names.index(field) + 1)

    return format_html(
        '<a class="sort-link{}" href="{}">{}{}{}</a>',
        " sort-active" if state else "",
        url,
        label,
        arrow,
        priority,
    )
