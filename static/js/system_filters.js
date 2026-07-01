/**
 * Инициализация фильтров расширенного поиска в списке/карточках систем:
 *  - «Класс системы» — одиночный выбор (пишет id в скрытый input);
 *  - «Объект», «Вендор» — мультивыбор с поиском;
 *  - «Статус», «Тип продукта» — мультивыбор без поля поиска.
 * Опирается на setupMultiFilterPicker из app.js.
 */
document.addEventListener('DOMContentLoaded', function () {
    // Класс системы — одиночный выбор.
    const classContainer = document.getElementById('classFilterPicker');
    const classHidden = document.getElementById('selectedClassFilter');
    if (classContainer && classHidden) {
        classContainer.querySelectorAll('.system-item').forEach(function (item) {
            item.addEventListener('click', function () {
                classContainer.querySelectorAll('.system-item').forEach(function (el) {
                    el.classList.remove('selected');
                });
                item.classList.add('selected');
                classHidden.value = item.getAttribute('data-id') || '';
            });
        });
    }

    setupMultiFilterPicker('objectFilterSearch', 'objectFilterBtn', 'objectFilterList', 'objectFilterInputs', 'objectFilterNoResults');
    setupMultiFilterPicker('vendorFilterSearch', 'vendorFilterBtn', 'vendorFilterList', 'vendorFilterInputs', 'vendorFilterNoResults');
    // Статус и тип продукта — без поля поиска (только выбор пунктов).
    setupMultiFilterPicker(null, null, 'statusFilterList', 'statusFilterInputs', null);
    setupMultiFilterPicker(null, null, 'ptypeFilterList', 'ptypeFilterInputs', null);
});
