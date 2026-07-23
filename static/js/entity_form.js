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

    /* Множественный выбор с капсулами (.capsule-picker) инициализируется
       общей функцией initCapsulePicker в app.js. */

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

    /* ---- Редакторы строк «класс + индустрия» (select с опцией «Все») ----
       Универсальная механика для двух блоков:
        - компетенции инж. компании / ФПЦ (поля comp_class / comp_industry);
        - исключения системного интегратора (поля excl_class / excl_industry).
       Пустое значение (опция «— Все —») допустимо: класс и индустрия nullable. */
    (function () {
        const jsonEl = function (id) { const e = document.getElementById(id); try { return e ? JSON.parse(e.textContent) : []; } catch (x) { return []; } };
        const CLASSES = jsonEl('competencyClassesData');
        const INDUSTRIES = jsonEl('competencyIndustriesData');

        function makeSelect(options, fieldName, allLabel, preId) {
            const sel = document.createElement('select');
            sel.name = fieldName;
            const optAll = document.createElement('option');
            optAll.value = ''; optAll.textContent = allLabel;
            sel.appendChild(optAll);
            options.forEach(function (o) {
                const op = document.createElement('option');
                op.value = String(o.id); op.textContent = o.label;
                if (preId !== undefined && preId !== null && preId !== '' && String(o.id) === String(preId)) {
                    op.selected = true;
                }
                sel.appendChild(op);
            });
            return sel;
        }

        function initEditor(listId, addBtnId, dataId, classField, industryField) {
            const list = document.getElementById(listId);
            const addBtn = document.getElementById(addBtnId);
            if (!list || !addBtn) return;
            const EXISTING = jsonEl(dataId);

            function makeRow(preClassId, preIndustryId) {
                const row = document.createElement('div'); row.className = 'kv-row';
                row.appendChild(makeSelect(CLASSES, classField, '— Все классы —', preClassId));
                row.appendChild(makeSelect(INDUSTRIES, industryField, '— Все отрасли —', preIndustryId));
                const rm = document.createElement('button');
                rm.type = 'button'; rm.className = 'btn btn-danger btn-sm kv-remove'; rm.title = 'Удалить';
                rm.textContent = '\u2212';
                rm.addEventListener('click', function () { row.remove(); });
                row.appendChild(rm);
                return row;
            }

            EXISTING.forEach(function (p) { list.appendChild(makeRow(p.class_id, p.industry_id)); });
            addBtn.addEventListener('click', function () { list.appendChild(makeRow()); });
        }

        // Компетенции инж. компании / ФПЦ.
        initEditor('competencyList', 'competencyAddBtn', 'competencyExistingData', 'comp_class', 'comp_industry');
        // Исключения системного интегратора («от обратного»).
        initEditor('exclusionList', 'exclusionAddBtn', 'exclusionExistingData', 'excl_class', 'excl_industry');
    })();


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

    /* ---- Показ блоков по типу участника ----
       Блок, недоступный для выбранного типа, полностью скрывается, а его поля
       отключаются (disabled), чтобы неприменимые значения не уходили в POST.
       Учитываем вложенные .type-block: поле активно, только если видимы ВСЕ
       охватывающие его type-block'и. */
    const typeSelect = document.getElementById('entityTypeSelect');
    function blockMatches(b, t) {
        const types = (b.getAttribute('data-for') || '').split(' ');
        return types.indexOf(t) !== -1;
    }
    function refreshTypeBlocks() {
        const t = typeSelect ? typeSelect.value : '';
        document.querySelectorAll('.type-block').forEach(function (b) {
            b.style.display = blockMatches(b, t) ? '' : 'none';
        });
        // Отключаем поля внутри любого скрытого (в т.ч. родительского) type-block.
        document.querySelectorAll('.type-block').forEach(function (b) {
            let visible = blockMatches(b, t);
            let anc = b.parentElement;
            while (anc && visible) {
                if (anc.classList && anc.classList.contains('type-block')) {
                    visible = blockMatches(anc, t);
                }
                anc = anc.parentElement;
            }
            b.querySelectorAll('input, select, textarea').forEach(function (el) {
                el.disabled = !visible;
            });
        });
    }
    if (typeSelect) { typeSelect.addEventListener('change', refreshTypeBlocks); refreshTypeBlocks(); }
});
