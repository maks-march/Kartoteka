function toggleAdvanced(el) {
    const advancedSection = document.getElementById('advancedSearch');
    if (!advancedSection) return;
    advancedSection.classList.toggle('show');

    if (advancedSection.classList.contains('show')) {
        el.textContent = 'Скрыть поиск \u25B2';
    } else {
        el.textContent = 'Расширенный поиск \u25BC';
    }
}

window.addEventListener('load', function() {
    const advancedSection = document.getElementById('advancedSearch');
    if (!advancedSection) return;
    const urlParams = new URLSearchParams(window.location.search);

    // Собираем имена всех фильтров, находящихся ВНУТРИ блока расширенного поиска:
    // из name у полей и из data-name у контейнеров скрытых input'ов.
    const names = new Set();
    advancedSection.querySelectorAll('[name]').forEach(function(el) {
        const n = el.getAttribute('name');
        if (n) names.add(n);
    });
    advancedSection.querySelectorAll('[data-name]').forEach(function(el) {
        const n = el.getAttribute('data-name');
        if (n) names.add(n);
    });

    // Раскрываем блок, если хотя бы один из этих фильтров задействован в URL.
    let active = false;
    names.forEach(function(n) {
        if (urlParams.getAll(n).some(function(v) { return v !== ''; })) active = true;
    });

    if (active) {
        advancedSection.classList.add('show');
        const btn = document.querySelector('.btn-link[onclick^="toggleAdvanced"]');
        if (btn) btn.textContent = 'Скрыть поиск \u25B2';
    }
});

/* ===== Универсальный подпоиск-выбор из списка (.picker) =====
   Атрибуты контейнера .picker:
   - data-target       — селектор скрытого input, куда пишется id выбранного элемента
   - data-enable       — селектор кнопки submit, активируемой после выбора (опционально)
   - data-level-source — селектор внешнего <select> уровня, фильтрующего список (опционально)
   Внутри: .picker-search, .picker-search-btn, .picker-level-filter (опционально),
   .picker-list со строками .system-item (data-id, data-name, data-level, data-keep)
   и заглушкой .picker-no-results */
function initPicker(picker) {
    const hiddenInput = document.querySelector(picker.getAttribute('data-target') || '');
    if (!hiddenInput) return;

    const submitBtn = picker.getAttribute('data-enable')
        ? document.querySelector(picker.getAttribute('data-enable')) : null;
    const levelSource = picker.getAttribute('data-level-source')
        ? document.querySelector(picker.getAttribute('data-level-source')) : null;
    const searchInput = picker.querySelector('.picker-search');
    const searchBtn = picker.querySelector('.picker-search-btn');
    const levelFilter = picker.querySelector('.picker-level-filter');
    const items = Array.from(picker.querySelectorAll('.system-item'));
    const noResults = picker.querySelector('.picker-no-results');

    function currentLevel() {
        if (levelFilter && levelFilter.value) return levelFilter.value;
        if (levelSource && levelSource.value) return levelSource.value;
        return '';
    }

    // Функция фильтрации (по названию и, если задан, по уровню)
    function applyFilter() {
        const q = searchInput ? searchInput.value.toLowerCase().trim() : '';
        const lvl = currentLevel();
        let hasVisible = false;

        items.forEach(function(item) {
            // data-keep — элемент всегда видим (например, «Без категории»)
            if (item.hasAttribute('data-keep')) {
                item.style.display = 'flex';
                hasVisible = true;
                return;
            }
            const name = item.getAttribute('data-name') || '';
            const okName = name.includes(q);
            const okLevel = !lvl || item.getAttribute('data-level') === lvl;
            if (okName && okLevel) {
                item.style.display = 'flex';
                hasVisible = true;
            } else {
                item.style.display = 'none';
            }
        });

        if (noResults) noResults.style.display = hasVisible ? 'none' : 'block';
    }

    function clearSelection() {
        items.forEach(function(i) { i.classList.remove('selected'); });
        hiddenInput.value = '';
        const keepItem = items.find(function(i) { return i.getAttribute('data-id') === ''; });
        if (keepItem) keepItem.classList.add('selected');
    }

    // Поиск по нажатию кнопки
    if (searchBtn) searchBtn.addEventListener('click', applyFilter);

    // Поиск по Enter в поле ввода
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                applyFilter();
            }
        });
    }

    // Фильтр по уровню внутри пикера — сразу при смене
    if (levelFilter) levelFilter.addEventListener('change', applyFilter);

    // Внешний select уровня: фильтрует список и сбрасывает выбор, если он стал недоступен
    if (levelSource) {
        levelSource.addEventListener('change', function() {
            applyFilter();
            const sel = items.find(function(i) { return i.classList.contains('selected'); });
            if (sel && sel.style.display === 'none') clearSelection();
        });
    }

    // Сворачиваемый режим: заголовок с подписью выбранного значения
    const headerValue = picker.querySelector('.picker-header-value');
    const emptyText = (picker.getAttribute('data-empty-text') || 'Не указано');

    function updateHeaderValue(name) {
        if (!headerValue) return;
        if (name && name.trim()) {
            headerValue.textContent = name;
            headerValue.classList.remove('empty-value');
        } else {
            headerValue.textContent = emptyText;
            headerValue.classList.add('empty-value');
        }
    }

    // Инициализация подписи заголовка из уже выбранного пункта
    if (headerValue) {
        const preselected = items.find(function(i) { return i.classList.contains('selected'); });
        let preName = '';
        if (preselected && preselected.getAttribute('data-id')) {
            const nameEl = preselected.querySelector('.system-name');
            preName = nameEl ? nameEl.textContent.trim() : '';
        }
        updateHeaderValue(preName);
    }

    // Выбор элемента из списка
    items.forEach(function(item) {
        item.addEventListener('click', function() {
            items.forEach(function(i) { i.classList.remove('selected'); });
            this.classList.add('selected');
            hiddenInput.value = this.getAttribute('data-id');
            // Сообщаем внешним обработчикам о смене выбора (напр. классы подсистем).
            hiddenInput.dispatchEvent(new Event('change', { bubbles: true }));
            if (submitBtn) submitBtn.disabled = false;

            // Обновляем подпись заголовка и сворачиваем (для пустого пункта — «Не указано»)
            if (headerValue) {
                const nameEl = this.querySelector('.system-name');
                const isEmpty = !this.getAttribute('data-id');
                updateHeaderValue(isEmpty ? '' : (nameEl ? nameEl.textContent.trim() : ''));
                if (picker.classList.contains('collapsible')) {
                    picker.classList.remove('open');
                }
            }
        });
    });

    applyFilter();
}

/* ===== Сворачиваемый пикер: клик по заголовку раскрывает/прячет тело ===== */
function initCollapsiblePicker(picker) {
    const header = picker.querySelector('.picker-header');
    if (!header) return;
    header.addEventListener('click', function() {
        picker.classList.toggle('open');
    });
}

/* ===== Переключатель режимов (выбрать существующий / создать новый) ===== */
function initModeToggle(toggle) {
    const btns = Array.from(toggle.querySelectorAll('[data-mode]'));
    btns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            btns.forEach(function(b) { b.classList.remove('active'); });
            this.classList.add('active');
            const mode = this.getAttribute('data-mode');
            document.querySelectorAll('.mode-section').forEach(function(sec) {
                sec.style.display = sec.getAttribute('data-mode') === mode ? '' : 'none';
            });
        });
    });
}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.picker').forEach(initPicker);
    document.querySelectorAll('.picker.collapsible').forEach(initCollapsiblePicker);
    document.querySelectorAll('.mode-toggle').forEach(initModeToggle);
});

/* ===== Множественный выбор в фильтрах-пикерах =====
   Позволяет выбрать несколько пунктов списка. Для каждого выбранного
   элемента в контейнере inputsContainer создаётся <input type="hidden">
   с именем inputsContainer.dataset.name и значением data-id пункта.
   Пункт «Все ...» (data-id="") сбрасывает выбор. */
function setupMultiFilterPicker(searchId, btnId, listId, inputsContainerId, noResultsId) {
    const searchInput = document.getElementById(searchId);
    const searchBtn = document.getElementById(btnId);
    const list = document.getElementById(listId);
    const inputsContainer = document.getElementById(inputsContainerId);
    const noResults = document.getElementById(noResultsId);
    // searchInput может отсутствовать — фильтр работает только выбором пунктов.
    if (!list || !inputsContainer) return;

    const fieldName = inputsContainer.getAttribute('data-name');
    const items = Array.from(list.querySelectorAll('.system-item'));
    const allItem = items.find(i => i.getAttribute('data-id') === '');

    // Перестраиваем скрытые input'ы по выделенным пунктам
    function syncInputs() {
        inputsContainer.innerHTML = '';
        items.forEach(item => {
            const id = item.getAttribute('data-id');
            if (id && item.classList.contains('selected')) {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = fieldName;
                input.value = id;
                inputsContainer.appendChild(input);
            }
        });
    }

    // Подсветка пункта «Все ...» когда ничего конкретного не выбрано
    function syncAllItem() {
        if (!allItem) return;
        const anySelected = items.some(i => i.getAttribute('data-id') && i.classList.contains('selected'));
        allItem.classList.toggle('selected', !anySelected);
    }

    function filterItems() {
        const query = (searchInput ? searchInput.value : '').toLowerCase().trim();
        let hasVisible = false;
        items.forEach(item => {
            const name = item.getAttribute('data-name');
            // пункт "Все ..." (без data-name) показываем всегда
            if (name === null || name.includes(query)) {
                item.style.display = 'flex';
                hasVisible = true;
            } else {
                item.style.display = 'none';
            }
        });
        if (noResults) noResults.style.display = hasVisible ? 'none' : 'block';
    }

    if (searchBtn) searchBtn.addEventListener('click', filterItems);
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') { e.preventDefault(); filterItems(); }
        });
    }

    items.forEach(item => {
        item.addEventListener('click', function() {
            const id = this.getAttribute('data-id');
            if (id === '') {
                // «Все ...» — снимаем все выделения
                items.forEach(i => i.classList.remove('selected'));
            } else {
                this.classList.toggle('selected');
            }
            syncAllItem();
            syncInputs();
        });
    });

    syncAllItem();
    syncInputs();
}

/* ===== Сворачиваемые фильтры в формах поиска =====
   Структура:
   <div class="filter-collapse">
     <div class="filter-collapse-header"> <label/> <значение/> <каретка/> </div>
     <div class="filter-collapse-body"> ... поиск/список ... </div>
   </div>
   По клику на header переключается класс .open на контейнере. */
function initFilterCollapse(box) {
    const header = box.querySelector('.filter-collapse-header');
    if (!header) return;
    header.addEventListener('click', function() {
        box.classList.toggle('open');
    });
}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.filter-collapse').forEach(initFilterCollapse);
});

/* ===== Клик по карточке = переход на её страницу =====
   Карточка с data-href ведёт на detail. Клик по вложенной ссылке
   (владелец/вендор и т.п.) работает как обычно и не перехватывается. */
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.entity-card[data-href]').forEach(function(card) {
        card.addEventListener('click', function(e) {
            if (e.target.closest('a')) return;      // клик по вложенной ссылке — не мешаем
            window.location.href = card.getAttribute('data-href');
        });
    });
});
