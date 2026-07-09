/**
 * Форма участника рынка.
 *  - динамические пары «ключ — значение» (контакты, фин. показатели);
 *  - показ блоков по типу участника;
 *  - переключатель партнёрства;
 *  - раскрываемые пикеры с автопоиском: одиночный выбор объекта (+ автозаполнение
 *    региона), множественный выбор продуктов (пишет id в hidden-инпуты);
 *  - компетенция по функции (пары «класс + индустрия»).
 * Пикер отраслей (.industry-picker) инициализируется в app.js.
 */
document.addEventListener('DOMContentLoaded', function () {

    /* ---- Пары «ключ — значение» (контакты, финансы) ---- */
    function makeRow(keyName, valueName) {
        const row = document.createElement('div');
        row.className = 'kv-row';
        row.innerHTML =
            '<input type="text" name="' + keyName + '" placeholder="Ключ">' +
            '<input type="text" name="' + valueName + '" placeholder="Значение">' +
            '<button type="button" class="btn btn-danger btn-sm kv-remove" title="Удалить">\u2212</button>';
        return row;
    }
    document.querySelectorAll('.kv-add').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const list = document.querySelector(btn.getAttribute('data-target'));
            if (list) list.appendChild(makeRow(btn.getAttribute('data-key'), btn.getAttribute('data-value')));
        });
    });
    document.addEventListener('click', function (e) {
        const rm = e.target.closest('.kv-remove');
        if (rm) { const row = rm.closest('.kv-row'); if (row) row.remove(); }
    });

    /* ---- Автопоиск внутри пикера ---- */
    function wireSearch(picker) {
        const search = picker.querySelector('.picker-search');
        if (!search) return;
        const items = Array.from(picker.querySelectorAll('.system-item'));
        const noRes = picker.querySelector('.picker-empty');
        search.addEventListener('input', function () {
            const q = search.value.toLowerCase().trim();
            let any = false;
            items.forEach(function (it) {
                if (it.hasAttribute('data-keep')) { it.style.display = ''; any = true; return; }
                const ok = (it.getAttribute('data-name') || '').includes(q);
                it.style.display = ok ? '' : 'none';
                if (ok) any = true;
            });
            if (noRes) noRes.style.display = any ? 'none' : 'block';
        });
    }
    /* ---- Раскрытие/сворачивание по заголовку ---- */
    function wireCollapse(picker) {
        const header = picker.querySelector('.picker-header');
        if (header) header.addEventListener('click', function (e) {
            if (!e.target.closest('.picker-body')) picker.classList.toggle('open');
        });
    }

    /* ---- Множественный выбор с капсулами (продукты) ----
       Заголовок показывает выбранное нейтральными капсулами (крестик снимает
       выбор), список — в нашем стиле с автопоиском и группами (data-group). */
    document.querySelectorAll('.capsule-picker').forEach(function (picker) {
        const header = picker.querySelector('.picker-header');
        const chips = picker.querySelector('.picker-chips');
        const emptyText = picker.getAttribute('data-empty-text') || 'Не выбрано';
        const search = picker.querySelector('.picker-search');
        const list = picker.querySelector('.system-results-container');
        // Контейнер скрытых input'ов — прямой потомок пикера с data-name
        // (у .system-item тоже есть data-name, поэтому ищем именно вне списка).
        const inputsBox = picker.querySelector(':scope > [data-name]');
        const noRes = picker.querySelector('.picker-empty');
        if (!inputsBox || !list) return;
        const fieldName = inputsBox.getAttribute('data-name');
        const items = Array.from(list.querySelectorAll('.system-item'));
        const groupLabels = Array.from(list.querySelectorAll('.group-label'));

        function itemById(id) { return items.find(function (i) { return i.getAttribute('data-id') === id; }); }

        function sync() {
            inputsBox.innerHTML = '';
            const selected = items.filter(function (i) { return i.classList.contains('selected'); });
            selected.forEach(function (it) {
                const inp = document.createElement('input');
                inp.type = 'hidden'; inp.name = fieldName; inp.value = it.getAttribute('data-id');
                inputsBox.appendChild(inp);
            });
            if (chips) {
                chips.innerHTML = '';
                if (!selected.length) {
                    const e = document.createElement('span');
                    e.className = 'empty-value'; e.textContent = emptyText;
                    chips.appendChild(e);
                } else {
                    selected.forEach(function (it) {
                        const chip = document.createElement('span');
                        chip.className = 'chip';
                        const nameEl = it.querySelector('.system-name');
                        const name = nameEl ? nameEl.textContent.trim() : (it.getAttribute('data-name') || '');
                        const label = document.createElement('span'); label.textContent = name;
                        const x = document.createElement('span'); x.className = 'x'; x.textContent = '\u2715';
                        x.setAttribute('data-id', it.getAttribute('data-id'));
                        chip.appendChild(label); chip.appendChild(x);
                        chips.appendChild(chip);
                    });
                }
            }
        }

        // раскрытие/сворачивание (клик по крестику капсулы не сворачивает)
        if (header) header.addEventListener('click', function (e) {
            if (e.target.closest('.picker-body')) return;
            if (e.target.classList.contains('x')) return;
            picker.classList.toggle('open');
        });

        // выбор пункта
        items.forEach(function (it) {
            it.addEventListener('click', function () { it.classList.toggle('selected'); sync(); });
        });

        // снятие капсулы крестиком
        if (chips) chips.addEventListener('click', function (e) {
            if (!e.target.classList.contains('x')) return;
            e.stopPropagation();
            const it = itemById(e.target.getAttribute('data-id'));
            if (it) { it.classList.remove('selected'); sync(); }
        });

        // автопоиск (+ скрытие пустых групп)
        if (search) search.addEventListener('input', function () {
            const q = search.value.toLowerCase().trim();
            let any = false;
            items.forEach(function (it) {
                const ok = (it.getAttribute('data-name') || '').includes(q);
                it.style.display = ok ? '' : 'none';
                if (ok) any = true;
            });
            groupLabels.forEach(function (lbl) {
                const g = lbl.getAttribute('data-group');
                const visible = items.some(function (o) {
                    return o.getAttribute('data-group') === g && o.style.display !== 'none';
                });
                lbl.style.display = visible ? '' : 'none';
            });
            if (noRes) noRes.style.display = any ? 'none' : 'block';
        });

        sync();
    });

    /* ---- Одиночный выбор объекта (+ автозаполнение региона) ---- */
    const regionInput = document.getElementById('regionInput');
    let regionTouched = false;
    if (regionInput) regionInput.addEventListener('input', function () { regionTouched = true; });

    document.querySelectorAll('.single-id-picker').forEach(function (picker) {
        wireCollapse(picker); wireSearch(picker);
        const hidden = picker.querySelector('input[type="hidden"]');
        const headerValue = picker.querySelector('.picker-header-value');
        const emptyText = picker.getAttribute('data-empty-text') || 'Не выбрано';
        const items = Array.from(picker.querySelectorAll('.system-item'));

        function sync() {
            const sel = items.find(function (i) { return i.classList.contains('selected'); });
            const name = sel && sel.getAttribute('data-id')
                ? sel.querySelector('.system-name').textContent.trim() : '';
            if (headerValue) {
                if (name) { headerValue.textContent = name; headerValue.classList.remove('empty-value'); }
                else { headerValue.textContent = emptyText; headerValue.classList.add('empty-value'); }
            }
        }
        items.forEach(function (it) {
            it.addEventListener('click', function () {
                items.forEach(function (x) { x.classList.remove('selected'); });
                it.classList.add('selected');
                if (hidden) hidden.value = it.getAttribute('data-id') || '';
                picker.classList.remove('open');
                sync();
                // Автозаполнение региона из выбранного объекта (если не правили вручную)
                if (regionInput) {
                    const region = it.getAttribute('data-region') || '';
                    if (region && (!regionTouched || regionInput.value === '')) regionInput.value = region;
                }
            });
        });
        sync();
    });

    /* ---- Компетенция по функции: строки «класс + индустрия» ----
       Оба поля — combobox «только из списка»: подсказки снизу в нашем стиле,
       свой вариант ввести нельзя (невалидный ввод → предупреждение и откат к
       последнему выбранному). Класс шлёт id, индустрия — название. */
    const compAdd = document.getElementById('competencyAddBtn');
    const compList = document.getElementById('competencyList');
    if (compAdd && compList) {
        const jsonEl = function (id) { const e = document.getElementById(id); try { return e ? JSON.parse(e.textContent) : []; } catch (x) { return []; } };
        const CLASSES = jsonEl('competencyClassesData');
        const INDUSTRIES = jsonEl('competencyIndustriesData').map(function (n) { return { id: n, label: n, desc: '' }; });
        const EXISTING = jsonEl('competencyExistingData');

        function makeCombo(options, fieldName, placeholder, warnText, preId) {
            const combo = document.createElement('div'); combo.className = 'combo';
            const input = document.createElement('input');
            input.type = 'text'; input.placeholder = placeholder; input.autocomplete = 'off';
            const hidden = document.createElement('input'); hidden.type = 'hidden'; hidden.name = fieldName; hidden.value = '';
            const panel = document.createElement('div'); panel.className = 'combo-panel';
            const empty = document.createElement('div'); empty.className = 'combo-empty'; empty.textContent = 'Ничего не найдено';
            const warn = document.createElement('div'); warn.className = 'combo-warn'; warn.textContent = warnText;
            let lastValid = { label: '', id: '' };

            const byLabel = function (txt) {
                return options.find(function (o) { return o.label.toLowerCase() === txt.trim().toLowerCase(); });
            };

            options.forEach(function (o) {
                const it = document.createElement('div'); it.className = 'system-item';
                it.setAttribute('data-label', o.label.toLowerCase());
                const name = document.createElement('span'); name.className = 'system-name'; name.textContent = o.label;
                it.appendChild(name);
                if (o.desc) { const d = document.createElement('span'); d.className = 'system-info'; d.textContent = o.desc; it.appendChild(d); }
                it.addEventListener('mousedown', function (e) {   // раньше blur
                    e.preventDefault();
                    input.value = o.label; hidden.value = o.id;
                    combo.classList.remove('open', 'invalid');
                    lastValid = { label: o.label, id: String(o.id) };
                });
                panel.appendChild(it);
            });
            panel.appendChild(empty);

            if (preId !== undefined && preId !== null && preId !== '') {
                const o = options.find(function (x) { return String(x.id) === String(preId); });
                if (o) { input.value = o.label; hidden.value = o.id; lastValid = { label: o.label, id: String(o.id) }; }
            }

            function filter() {
                const q = input.value.toLowerCase().trim(); let any = false;
                panel.querySelectorAll('.system-item').forEach(function (it) {
                    const ok = it.getAttribute('data-label').indexOf(q) !== -1;
                    it.style.display = ok ? '' : 'none'; if (ok) any = true;
                });
                empty.style.display = any ? 'none' : 'block';
            }
            input.addEventListener('focus', function () { combo.classList.remove('invalid'); combo.classList.add('open'); filter(); });
            input.addEventListener('input', function () { combo.classList.add('open'); combo.classList.remove('invalid'); hidden.value = ''; filter(); });
            input.addEventListener('blur', function () {
                setTimeout(function () {
                    combo.classList.remove('open');
                    if (input.value.trim() === '') { hidden.value = ''; lastValid = { label: '', id: '' }; combo.classList.remove('invalid'); return; }
                    const m = byLabel(input.value);
                    if (m) { hidden.value = String(m.id); input.value = m.label; lastValid = { label: m.label, id: String(m.id) }; combo.classList.remove('invalid'); }
                    else { combo.classList.add('invalid'); input.value = lastValid.label; hidden.value = lastValid.id; }
                }, 120);
            });

            combo.appendChild(input); combo.appendChild(hidden); combo.appendChild(panel); combo.appendChild(warn);
            return combo;
        }

        function makeRow(preClassId, preIndustry) {
            const row = document.createElement('div'); row.className = 'kv-row';
            row.appendChild(makeCombo(CLASSES, 'comp_class', 'Класс (выберите из списка)', 'Выберите класс из списка', preClassId));
            row.appendChild(makeCombo(INDUSTRIES, 'comp_industry', 'Индустрия (выберите из списка)', 'Выберите индустрию из списка', preIndustry));
            const rm = document.createElement('button');
            rm.type = 'button'; rm.className = 'btn btn-danger btn-sm kv-remove'; rm.title = 'Удалить';
            rm.textContent = '\u2212';
            rm.addEventListener('click', function () { row.remove(); });
            row.appendChild(rm);
            return row;
        }

        EXISTING.forEach(function (p) { compList.appendChild(makeRow(p.class_id, p.industry)); });
        compAdd.addEventListener('click', function () { compList.appendChild(makeRow()); });
    }

    /* ---- Переключатель партнёрства ---- */
    const pt = document.getElementById('partnerToggle');
    const ptValue = document.getElementById('isPartnerValue');
    if (pt && ptValue) {
        function toggle() {
            const on = pt.classList.toggle('on');
            pt.setAttribute('aria-checked', on ? 'true' : 'false');
            ptValue.value = on ? 'on' : 'off';
        }
        pt.addEventListener('click', toggle);
        pt.addEventListener('keydown', function (e) {
            if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); toggle(); }
        });
    }

    /* ---- Показ блоков по типу участника ---- */
    const typeSelect = document.getElementById('entityTypeSelect');
    function refreshTypeBlocks() {
        const t = typeSelect ? typeSelect.value : '';
        document.querySelectorAll('.type-block').forEach(function (b) {
            const types = (b.getAttribute('data-for') || '').split(' ');
            b.style.display = types.indexOf(t) !== -1 ? '' : 'none';
        });
    }
    if (typeSelect) { typeSelect.addEventListener('change', refreshTypeBlocks); refreshTypeBlocks(); }
});
