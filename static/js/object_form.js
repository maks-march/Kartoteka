/**
 * Логика формы объекта (создание/редактирование, а также режим «Создать
 * новый» в форме добавления ребёнка).
 *
 * Обеспечивает:
 *  - показ/скрытие выбора родителя в зависимости от уровня (у уровня 1 родителя нет);
 *  - показ поля «Кодовое расположение» (title) только для объектов 3-го уровня;
 *  - автоподстановку адреса выбранного родителя в пустые адресные поля.
 *
 * Данные адресов родителей передаются с сервера в JSON-блоке #parentAddresses.
 */
(function () {
    const levelSelect = document.getElementById('levelSelect');
    if (!levelSelect) return;

    const parentGroup = document.getElementById('parentGroup');
    const parentInput = document.getElementById('selectedParentId');
    const titleGroup = document.getElementById('titleGroup');
    const titleInput = document.getElementById('titleInput');

    let parentAddresses = {};
    const paEl = document.getElementById('parentAddresses');
    try {
        parentAddresses = JSON.parse((paEl && paEl.textContent) || '{}');
    } catch (e) {
        parentAddresses = {};
    }

    /** Скрывает выбор родителя для объектов 1-го уровня. */
    function toggleParent() {
        if (!parentGroup) return;
        const level = parseInt(levelSelect.value, 10);
        if (level === 1) {
            parentGroup.style.display = 'none';
            if (parentInput) parentInput.value = '';
        } else {
            parentGroup.style.display = '';
        }
    }

    /** title (кодовое расположение) редактируется только на 3-м уровне. */
    function toggleTitle() {
        if (!titleGroup) return;
        const level = parseInt(levelSelect.value, 10);
        if (level === 3) {
            titleGroup.style.display = '';
            if (titleInput) titleInput.disabled = false;
        } else {
            titleGroup.style.display = 'none';
            if (titleInput) {
                titleInput.value = '';
                titleInput.disabled = true;
            }
        }
    }

    /** Подставляет адрес выбранного родителя в пустые адресные поля. */
    function applyParentAddress() {
        if (!parentInput) return;
        const addr = parentAddresses[parentInput.value];
        if (!addr) return;
        document.querySelectorAll('.addr-field').forEach(function (field) {
            const key = field.getAttribute('data-addr');
            if (!field.value && addr[key]) field.value = addr[key];
        });
    }

    levelSelect.addEventListener('change', function () {
        toggleParent();
        toggleTitle();
    });

    // Пикер родителя пишет в скрытый input не через change, поэтому реагируем на клик.
    const parentPicker = document.getElementById('parentPicker');
    if (parentPicker) {
        parentPicker.addEventListener('click', function () {
            setTimeout(applyParentAddress, 0);
        });
    }

    toggleParent();
    toggleTitle();
})();
