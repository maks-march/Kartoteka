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
    // Пикер отраслей (множественный выбор) инициализируется в app.js.

    /* Множественный выбор с id (компетенция по продуктам):
       выбранные пункты (data-id) пишутся hidden-инпутами в контейнер,
       имя берётся из data-name контейнера. Заголовок показывает названия. */
    document.querySelectorAll('.multi-id-picker').forEach(function (picker) {
        const list = picker.querySelector('.system-results-container');
        const inputsBox = picker.querySelector('[data-name]');
        const headerValue = picker.querySelector('.picker-header-value');
        const emptyText = picker.getAttribute('data-empty-text') || 'Не выбрано';
        if (!list || !inputsBox) return;
        const fieldName = inputsBox.getAttribute('data-name');
        const items = Array.from(list.querySelectorAll('.system-item'));

        function sync() {
            inputsBox.innerHTML = '';
            const names = [];
            items.forEach(function (it) {
                if (it.classList.contains('selected')) {
                    const inp = document.createElement('input');
                    inp.type = 'hidden'; inp.name = fieldName; inp.value = it.getAttribute('data-id');
                    inputsBox.appendChild(inp);
                    const n = it.querySelector('.system-name');
                    if (n) names.push(n.textContent.trim());
                }
            });
            if (headerValue) {
                if (names.length) { headerValue.textContent = names.join(', '); headerValue.classList.remove('empty-value'); }
                else { headerValue.textContent = emptyText; headerValue.classList.add('empty-value'); }
            }
        }
        items.forEach(function (it) {
            it.addEventListener('click', function () { it.classList.toggle('selected'); sync(); });
        });
        sync();
    });

    /* Компетенция по функции: добавление строки «класс + индустрия». */
    const compAdd = document.getElementById('competencyAddBtn');
    const compList = document.getElementById('competencyList');
    if (compAdd && compList) {
        const tpl = document.querySelector(compAdd.getAttribute('data-classes-source'));
        compAdd.addEventListener('click', function () {
            const row = document.createElement('div');
            row.className = 'kv-row';
            const select = tpl ? tpl.cloneNode(true) : document.createElement('select');
            select.removeAttribute('id'); select.style.display = ''; select.name = 'comp_class';
            row.appendChild(select);
            const inp = document.createElement('input');
            inp.type = 'text'; inp.name = 'comp_industry'; inp.placeholder = 'Индустрия';
            inp.setAttribute('list', 'industryOptions');
            row.appendChild(inp);
            const rm = document.createElement('button');
            rm.type = 'button'; rm.className = 'btn btn-danger btn-sm kv-remove'; rm.title = 'Удалить';
            rm.textContent = '\u2212';
            row.appendChild(rm);
            compList.appendChild(row);
        });
    }

    /* Показ секции инжиниринговой компании только для соответствующего типа. */
    const typeSelect = document.getElementById('entityTypeSelect');
    const engSection = document.getElementById('engineeringSection');
    if (typeSelect && engSection) {
        typeSelect.addEventListener('change', function () {
            engSection.style.display = (typeSelect.value === 'engineering_company') ? '' : 'none';
        });
    }
});
