/**
 * Профиль пользователя: переключение вкладок и живой поиск по таблицам.
 * switchTab вызывается из разметки через onclick, поэтому объявлена глобально.
 */

/** Показывает выбранную вкладку и подсвечивает её кнопку. */
function switchTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(function (el) {
        el.style.display = 'none';
    });
    const pane = document.getElementById('tab-' + tabName);
    if (pane) pane.style.display = 'block';

    document.querySelectorAll('.tab-btn').forEach(function (btn) {
        btn.classList.remove('btn-primary', 'active');
        btn.classList.add('btn-secondary');
    });
    const activeBtn = document.querySelector('.tab-btn[data-tab="' + tabName + '"]');
    if (activeBtn) {
        activeBtn.classList.remove('btn-secondary');
        activeBtn.classList.add('btn-primary', 'active');
    }
}

// Живой поиск по таблицам профиля (по первому столбцу).
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.table-search').forEach(function (input) {
        input.addEventListener('input', function () {
            const table = document.getElementById(this.getAttribute('data-target'));
            if (!table) return;
            const q = this.value.toLowerCase();
            table.querySelectorAll('tbody tr').forEach(function (row) {
                const nameCell = row.querySelector('td:first-child');
                if (!nameCell) return;
                row.style.display = nameCell.textContent.toLowerCase().includes(q) ? '' : 'none';
            });
        });
    });
});
