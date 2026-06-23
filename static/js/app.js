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
    if (urlParams.has('category') || urlParams.has('system_class') || urlParams.has('system') || urlParams.has('object') || urlParams.has('owner_entity')) {
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

    // Выбор элемента из списка
    items.forEach(function(item) {
        item.addEventListener('click', function() {
            items.forEach(function(i) { i.classList.remove('selected'); });
            this.classList.add('selected');
            hiddenInput.value = this.getAttribute('data-id');
            if (submitBtn) submitBtn.disabled = false;
        });
    });

    applyFilter();
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
    if (!searchInput || !list || !inputsContainer) return;

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
        const query = searchInput.value.toLowerCase().trim();
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
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') { e.preventDefault(); filterItems(); }
    });

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
