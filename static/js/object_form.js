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
    const ownerGroup = document.getElementById('ownerGroup');
    const ownerInheritHint = document.getElementById('ownerInheritHint');
    const ownerInput = document.getElementById('selectedOwnerEntityId');

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

    /** title (титульный номер) редактируется на 2-м и 3-м уровне. */
    function toggleTitle() {
        if (!titleGroup) return;
        const level = parseInt(levelSelect.value, 10);
        if (level === 2 || level === 3) {
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

    /** Юр. лицо выбирается только на 1-м уровне; для L2/L3 наследуется от родителя. */
    function toggleOwner() {
        if (!ownerGroup) return;
        const level = parseInt(levelSelect.value, 10);
        if (level === 1) {
            ownerGroup.style.display = '';
            if (ownerInheritHint) ownerInheritHint.style.display = 'none';
        } else {
            ownerGroup.style.display = 'none';
            if (ownerInheritHint) ownerInheritHint.style.display = '';
            // Значение из формы не отправляем — владелец берётся от родителя на бэкенде.
            if (ownerInput) ownerInput.value = '';
        }
    }

    /** Подставляет адрес выбранного родителя в адресные поля.
     *
     * Отслеживает поля, заполненные автоматически (не тронутые пользователем):
     * при смене родителя они перезаписываются адресом нового родителя, а поля,
     * которые пользователь редактировал вручную, остаются без изменений.
     */
    const addrFields = Array.from(document.querySelectorAll('.addr-field'));

    // Помечаем поле как «тронутое вручную» при пользовательском вводе.
    addrFields.forEach(function (field) {
        field.addEventListener('input', function () {
            field.dataset.userEdited = '1';
        });
    });

    function applyParentAddress() {
        if (!parentInput) return;
        const addr = parentAddresses[parentInput.value] || {};
        addrFields.forEach(function (field) {
            const key = field.getAttribute('data-addr');
            const inherited = addr[key] || '';
            // Не трогаем поля, которые пользователь ввёл/изменил вручную,
            // а также непустые значения самого объекта (реальный адрес при
            // редактировании). Перезаписываем только пустые и ранее
            // автозаполненные поля — это чинит повторное заполнение при
            // смене родителя.
            const overwritable = !field.dataset.userEdited &&
                (field.value === '' || field.dataset.autofilled === '1');
            if (!overwritable) return;
            field.value = inherited;
            field.dataset.autofilled = inherited ? '1' : '';
        });
    }

    levelSelect.addEventListener('change', function () {
        toggleParent();
        toggleTitle();
        toggleOwner();
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
    toggleOwner();
})();
