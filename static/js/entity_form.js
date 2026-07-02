/**
 * Форма участника рынка: динамические пары «ключ — значение»
 * (контакты и финансовые показатели). Кнопки .kv-add добавляют строку,
 * .kv-remove — удаляют. Целевой контейнер и имена полей задаются через
 * data-target / data-key / data-value на кнопке добавления.
 */
document.addEventListener('DOMContentLoaded', function () {
    function makeRow(keyName, valueName) {
        const row = document.createElement('div');
        row.className = 'kv-row';
        row.innerHTML =
            '<input type="text" name="' + keyName + '" placeholder="Ключ">' +
            '<input type="text" name="' + valueName + '" placeholder="Значение">' +
            '<button type="button" class="btn btn-danger btn-sm kv-remove" title="Удалить">−</button>';
        return row;
    }

    document.querySelectorAll('.kv-add').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const list = document.querySelector(btn.getAttribute('data-target'));
            if (!list) return;
            list.appendChild(makeRow(btn.getAttribute('data-key'), btn.getAttribute('data-value')));
        });
    });

    // Удаление строки (делегирование, чтобы работало и для новых строк).
    document.addEventListener('click', function (e) {
        const rm = e.target.closest('.kv-remove');
        if (rm) {
            const row = rm.closest('.kv-row');
            if (row) row.remove();
        }
    });
});
