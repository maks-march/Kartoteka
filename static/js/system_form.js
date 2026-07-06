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
 * Классы подсистем: блок виден только когда выбран составной класс
 * (data-composite="1"). При выборе составного класса автоматически отмечается
 * включаемый класс (data-includes, напр. у MOM — MES). При смене основного
 * класса ранее отмеченные подсистемы очищаются (после подтверждения).
 */
(function () {
    const classHidden = document.getElementById('selectedClassId');
    const block = document.getElementById('subsystemsBlock');
    if (!classHidden || !block) return;

    // Пункты списка классов (содержат data-composite / data-includes).
    const classItems = Array.from(document.querySelectorAll('.system-item[data-composite]'));
    const checks = Array.from(block.querySelectorAll('input[name="subsystem_classes"]'));

    function itemById(id) {
        return classItems.find(function (i) { return i.getAttribute('data-id') === String(id); });
    }
    function setChecked(clsId, val) {
        const cb = checks.find(function (c) { return c.value === String(clsId); });
        if (cb) cb.checked = val;
    }
    function clearAllChecks() {
        checks.forEach(function (c) { c.checked = false; });
    }
    function currentIsComposite(id) {
        const it = itemById(id);
        return it && it.getAttribute('data-composite') === '1';
    }

    // Прячем чекбокс класса, совпадающего с основным (нельзя быть подсистемой себя).
    function hideSelfCheckbox(id) {
        block.querySelectorAll('.subsystem-check').forEach(function (lbl) {
            lbl.style.display = (lbl.getAttribute('data-cls-id') === String(id)) ? 'none' : '';
        });
    }

    let prevId = classHidden.value;

    function refresh(auto) {
        const id = classHidden.value;
        if (currentIsComposite(id)) {
            block.style.display = '';
            hideSelfCheckbox(id);
            // Авто-подстановка включаемого класса (MOM -> MES) при выборе класса.
            if (auto) {
                const it = itemById(id);
                const inc = it ? it.getAttribute('data-includes') : '';
                if (inc) setChecked(inc, true);
            }
        } else {
            block.style.display = 'none';
        }
    }

    // Реакция на смену основного класса.
    classHidden.addEventListener('change', function () {
        const newId = classHidden.value;
        if (newId === prevId) return;
        // Если были отмеченные подсистемы — подтверждаем очистку при смене класса.
        const hadChecked = checks.some(function (c) { return c.checked; });
        if (hadChecked && !confirm('Сменить класс системы? Ранее выбранные классы подсистем будут очищены.')) {
            // откат выбора класса к предыдущему
            classHidden.value = prevId;
            const prevItem = itemById(prevId);
            document.querySelectorAll('.picker[data-target="#selectedClassId"] .system-item')
                .forEach(function (i) { i.classList.remove('selected'); });
            if (prevItem) prevItem.classList.add('selected');
            return;
        }
        clearAllChecks();
        prevId = newId;
        refresh(true);
    });

    // Инициализация при загрузке (без авто-очистки/подстановки поверх сохранённых).
    refresh(false);
})();
