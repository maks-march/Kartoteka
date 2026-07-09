/**
 * Инициализация фильтров расширенного поиска в списке/карточках систем:
 *  - «Класс системы» — одиночный выбор (пишет id в скрытый input);
 *  - «Объект», «Продукт» — мультивыбор с поиском;
 *  - «Статус» — мультивыбор без поля поиска.
 * Опирается на setupMultiFilterPicker из app.js.
 */
document.addEventListener('DOMContentLoaded', function () {
    // Класс системы — одиночный выбор + автопоиск по списку.
    const classContainer = document.getElementById('classFilterPicker');
    const classHidden = document.getElementById('selectedClassFilter');
    if (classContainer && classHidden) {
        const classItems = Array.from(classContainer.querySelectorAll('.system-item'));
        classItems.forEach(function (item) {
            item.addEventListener('click', function () {
                classItems.forEach(function (el) { el.classList.remove('selected'); });
                item.classList.add('selected');
                classHidden.value = item.getAttribute('data-id') || '';
            });
        });
        // Автопоиск по мере ввода.
        const classSearch = document.getElementById('classFilterSearch');
        const classNoRes = document.getElementById('classFilterNoResults');
        if (classSearch) {
            classSearch.addEventListener('input', function () {
                const q = classSearch.value.toLowerCase().trim();
                let any = false;
                classItems.forEach(function (it) {
                    if (it.hasAttribute('data-keep')) { it.style.display = ''; any = true; return; }
                    const ok = (it.getAttribute('data-name') || '').includes(q);
                    it.style.display = ok ? '' : 'none';
                    if (ok) any = true;
                });
                if (classNoRes) classNoRes.style.display = any ? 'none' : 'block';
            });
        }
    }

    setupMultiFilterPicker('objectFilterSearch', 'objectFilterBtn', 'objectFilterList', 'objectFilterInputs', 'objectFilterNoResults');
    setupMultiFilterPicker('productFilterSearch', 'productFilterBtn', 'productFilterList', 'productFilterInputs', 'productFilterNoResults');
    // Статус — без поля поиска (только выбор пунктов).
    setupMultiFilterPicker(null, null, 'statusFilterList', 'statusFilterInputs', null);
});
