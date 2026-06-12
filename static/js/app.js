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
    if (urlParams.has('category') || urlParams.has('system_class')) {
        advancedSection.classList.add('show');
        const btn = document.querySelector('.btn-link[onclick^="toggleAdvanced"]');
        if (btn) btn.textContent = 'Скрыть поиск \u25B2';
    }
});

/* ===== Форма привязки (объект <-> система): поиск и выбор из списка ===== */
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('systemSearchInput');
    const searchBtn = document.getElementById('searchBtn');
    const systemItems = document.querySelectorAll('.system-item');
    const hiddenInput = document.getElementById('selectedSystemId');
    const submitBtn = document.getElementById('submitBtn');
    const noResults = document.getElementById('noResults');

    if (!searchInput || !hiddenInput) return;

    // Функция фильтрации
    function filterSystems() {
        const query = searchInput.value.toLowerCase().trim();
        let hasVisible = false;

        systemItems.forEach(item => {
            const name = item.getAttribute('data-name');
            if (name.includes(query)) {
                item.style.display = 'flex';
                hasVisible = true;
            } else {
                item.style.display = 'none';
            }
        });

        if (noResults) noResults.style.display = hasVisible ? 'none' : 'block';
    }

    // Поиск по нажатию кнопки
    if (searchBtn) searchBtn.addEventListener('click', filterSystems);

    // Поиск по Enter в поле ввода
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            filterSystems();
        }
    });

    // Выбор элемента из списка
    systemItems.forEach(item => {
        item.addEventListener('click', function() {
            // Убираем выделение у всех
            systemItems.forEach(i => i.classList.remove('selected'));
            // Выделяем текущий
            this.classList.add('selected');
            // Записываем ID в скрытое поле
            hiddenInput.value = this.getAttribute('data-id');
            // Активируем кнопку отправки
            if (submitBtn) submitBtn.disabled = false;
        });
    });
});
