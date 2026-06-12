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
