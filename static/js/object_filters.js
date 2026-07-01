/**
 * Инициализация фильтров расширенного поиска в списке/карточках объектов
 * (мультивыбор: категория, юридическое лицо, привязанная система).
 * Опирается на setupMultiFilterPicker из app.js.
 */
document.addEventListener('DOMContentLoaded', function () {
    setupMultiFilterPicker('categoryFilterSearch', 'categoryFilterBtn', 'categoryFilterList', 'categoryFilterInputs', 'categoryFilterNoResults');
    setupMultiFilterPicker('ownerEntityFilterSearch', 'ownerEntityFilterBtn', 'ownerEntityFilterList', 'ownerEntityFilterInputs', 'ownerEntityFilterNoResults');
    setupMultiFilterPicker('systemFilterSearch', 'systemFilterBtn', 'systemFilterList', 'systemFilterInputs', 'systemFilterNoResults');
});
