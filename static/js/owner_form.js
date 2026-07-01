/**
 * Форма юридического лица: живой поиск по выпадающим спискам владельца и
 * корневого владельца (фильтрует <option> по введённому тексту).
 */
(function () {
    /** Привязывает фильтрацию опций select к текстовому полю поиска. */
    function setupSelectSearch(inputId, selectId) {
        const input = document.getElementById(inputId);
        const select = document.getElementById(selectId);
        if (!input || !select) return;
        input.addEventListener('input', function () {
            const q = this.value.toLowerCase();
            Array.from(select.options).forEach(function (opt) {
                const name = opt.getAttribute('data-name') || '';
                opt.style.display = (!opt.value || name.includes(q)) ? '' : 'none';
            });
        });
    }

    setupSelectSearch('ownerSearch', 'ownerSelect');
    setupSelectSearch('ultimateOwnerSearch', 'ultimateOwnerSelect');
})();
