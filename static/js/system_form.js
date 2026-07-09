/**
 * Форма системы: динамическое управление парами «характеристика — значение»
 * (технические характеристики). Кнопка добавляет новую строку, крестик удаляет.
 * Значения отправляются параллельными массивами spec_key[] / spec_value[].
 */
(function () {
    const list = document.getElementById('specsList');
    const addBtn = document.getElementById('specsAddBtn');
    if (!list || !addBtn) return;

    /** Создаёт новую строку пары ключ/значение. */
    function makeRow() {
        const row = document.createElement('div');
        row.className = 'kv-row';
        row.innerHTML =
            '<input type="text" name="spec_key" placeholder="Характеристика">' +
            '<input type="text" name="spec_value" placeholder="Значение">' +
            '<button type="button" class="btn btn-danger btn-sm kv-remove" title="Удалить">\u2212</button>';
        return row;
    }

    addBtn.addEventListener('click', function () {
        list.appendChild(makeRow());
    });

    // Удаление строки через делегирование клика.
    list.addEventListener('click', function (e) {
        const btn = e.target.closest('.kv-remove');
        if (btn) btn.closest('.kv-row').remove();
    });
})();


/**
 * Классы подсистем (крупные блоки-мультивыбор) — общий для форм системы и продукта.
 * Каждый блок .subsystems-block описывается data-атрибутами:
 *   data-class-input   — селектор скрытого input основного класса
 *   data-class-picker  — селектор пикера выбора основного класса
 *   data-list          — селектор контейнера со списком .system-item
 *   data-inputs        — селектор контейнера для скрытых input'ов подсистем
 *   data-search / data-search-btn / data-no-results — поиск (опционально)
 * Блок виден только для составного основного класса (data-composite="1").
 * Доступны только классы того же уровня, кроме самого основного и других
 * составных. При выборе составного авто-отмечается includes (MOM -> MES).
 * При смене основного класса выбор очищается (после подтверждения).
 */
function initSubsystemsBlock(block) {
    const classHidden = document.querySelector(block.getAttribute('data-class-input') || '');
    const list = document.querySelector(block.getAttribute('data-list') || '');
    const inputs = document.querySelector(block.getAttribute('data-inputs') || '');
    if (!classHidden || !list || !inputs) return;

    const searchInput = document.querySelector(block.getAttribute('data-search') || '');
    const searchBtn = document.querySelector(block.getAttribute('data-search-btn') || '');
    const noResults = document.querySelector(block.getAttribute('data-no-results') || '');
    const classItems = Array.from(
        document.querySelectorAll((block.getAttribute('data-class-picker') || '') + ' .system-item')
    );
    const items = Array.from(list.querySelectorAll('.system-item'));

    function classItemById(id) {
        return classItems.find(function (i) { return i.getAttribute('data-id') === String(id); });
    }
    function primaryIsComposite(id) {
        const it = classItemById(id);
        return it && it.getAttribute('data-composite') === '1';
    }

    function syncInputs() {
        inputs.innerHTML = '';
        items.forEach(function (item) {
            const id = item.getAttribute('data-id');
            if (id && item.classList.contains('selected') && item.style.display !== 'none') {
                const inp = document.createElement('input');
                inp.type = 'hidden';
                inp.name = 'subsystem_classes';
                inp.value = id;
                inputs.appendChild(inp);
            }
        });
    }

    // Доступность: тот же уровень, не сам основной, не составной. Недоступные скрыть и снять выбор.
    function applyEligibility() {
        const primaryId = classHidden.value;
        const primaryItem = classItemById(primaryId);
        const level = primaryItem ? primaryItem.getAttribute('data-level') : null;
        const query = (searchInput ? searchInput.value : '').toLowerCase().trim();
        let hasVisible = false;

        items.forEach(function (item) {
            const sameLevel = level !== null && item.getAttribute('data-level') === level;
            const isSelf = item.getAttribute('data-id') === String(primaryId);
            const isComposite = item.getAttribute('data-composite') === '1';
            const eligible = sameLevel && !isSelf && !isComposite;
            const matchesSearch = item.getAttribute('data-name').includes(query);

            if (eligible && matchesSearch) {
                item.style.display = 'flex';
                hasVisible = true;
            } else {
                item.style.display = 'none';
                if (!eligible) item.classList.remove('selected');
            }
        });
        if (noResults) noResults.style.display = hasVisible ? 'none' : 'block';
    }

    items.forEach(function (item) {
        item.addEventListener('click', function () {
            if (item.style.display === 'none') return;
            item.classList.toggle('selected');
            syncInputs();
        });
    });

    if (searchBtn) searchBtn.addEventListener('click', applyEligibility);
    if (searchInput) {
        // Автопоиск по мере ввода
        searchInput.addEventListener('input', applyEligibility);
        searchInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') { e.preventDefault(); applyEligibility(); }
        });
    }

    let prevId = classHidden.value;

    function refresh(auto) {
        const id = classHidden.value;
        if (primaryIsComposite(id)) {
            block.style.display = '';
            applyEligibility();
            if (auto) {
                const it = classItemById(id);
                const inc = it ? it.getAttribute('data-includes') : '';
                if (inc) {
                    const incItem = items.find(function (i) { return i.getAttribute('data-id') === String(inc); });
                    if (incItem && incItem.style.display !== 'none') incItem.classList.add('selected');
                }
            }
            syncInputs();
        } else {
            block.style.display = 'none';
            items.forEach(function (i) { i.classList.remove('selected'); });
            syncInputs();
        }
    }

    classHidden.addEventListener('change', function () {
        const newId = classHidden.value;
        if (newId === prevId) return;
        const hadSelected = items.some(function (i) { return i.classList.contains('selected'); });
        if (hadSelected && !confirm('Сменить класс? Ранее выбранные классы подсистем будут очищены.')) {
            classHidden.value = prevId;
            classItems.forEach(function (i) { i.classList.remove('selected'); });
            const prevItem = classItemById(prevId);
            if (prevItem) prevItem.classList.add('selected');
            return;
        }
        items.forEach(function (i) { i.classList.remove('selected'); });
        prevId = newId;
        refresh(true);
    });

    refresh(false);
}

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.subsystems-block').forEach(initSubsystemsBlock);
});
