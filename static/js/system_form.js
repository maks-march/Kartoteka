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
