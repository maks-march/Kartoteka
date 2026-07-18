"""Шаблонные фильтры карточки участника (цвет тегов компетенций и т.п.).

Правило цвета тега компетенции «по функции» (пара класс · индустрия):
- есть класс и есть отрасль → цвет по уровню автоматизации класса
  (``tag-0`` … ``tag-4`` — как в сводке систем);
- есть класс, но отрасль пустая («Все отрасли») → бирюзовый (``tag-teal``);
- класс пустой («Все классы»), задана только отрасль → серый (``tag-muted``).

Правило единое для инжиниринговой компании и вендора полного цикла.
Исключения системного интегратора («кроме: …») сюда НЕ попадают —
они всегда красные (``tag-danger``) и красятся прямо в шаблоне.
"""
from django import template

register = template.Library()


@register.filter
def competency_tag_class(competency):
    """CSS-класс тега компетенции «по функции» по правилу уровней/«Все».

    Аргумент — экземпляр EngineeringCompanyFunctionCompetency или
    FullCycleFunctionCompetency (нужны поля ``system_class`` и ``industry``,
    оба nullable).
    """
    system_class = getattr(competency, "system_class", None)
    industry = getattr(competency, "industry", None)

    # Только отрасль (класс = «Все классы») → серый.
    if system_class is None:
        return "tag-muted"

    # Есть класс, отрасль пустая («Все отрасли») → бирюзовый.
    if industry is None:
        return "tag-teal"

    # Класс + отрасль → цвет по уровню автоматизации класса.
    return f"tag-{system_class.level}"
