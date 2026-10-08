
// Sidebar toggle: collapses on desktop, opens as an off-canvas drawer on mobile.
const MOBILE_QUERY = window.matchMedia('(max-width: 768px)');

function safeStorage(action, key, value) {
    try {
        if (action === 'get') return localStorage.getItem(key);
        localStorage.setItem(key, value);
    } catch (e) { /* storage unavailable (private mode) — ignore */ }
    return null;
}

function setToggleExpanded() {
    const sidebar = document.querySelector('.sidebar');
    const toggle = document.getElementById('sidebarToggle');
    if (!sidebar || !toggle) return;
    const expanded = MOBILE_QUERY.matches ? sidebar.classList.contains('open') : !sidebar.classList.contains('collapsed');
    toggle.setAttribute('aria-expanded', String(expanded));
}

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;

    if (MOBILE_QUERY.matches) {
        sidebar.classList.toggle('open');
    } else {
        sidebar.classList.toggle('collapsed');
        safeStorage('set', 'sidebarCollapsed', sidebar.classList.contains('collapsed'));
    }
    setToggleExpanded();
}

function closeMobileSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) sidebar.classList.remove('open');
    setToggleExpanded();
}

// Restore sidebar state on page load
document.addEventListener('DOMContentLoaded', function () {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;

    if (safeStorage('get', 'sidebarCollapsed') === 'true') {
        sidebar.classList.add('collapsed');
    }

    // Backdrop that closes the drawer on mobile
    const backdrop = document.createElement('div');
    backdrop.className = 'sidebar-backdrop';
    backdrop.addEventListener('click', closeMobileSidebar);
    sidebar.insertAdjacentElement('afterend', backdrop);

    const toggle = document.getElementById('sidebarToggle');
    if (toggle) {
        toggle.setAttribute('aria-label', 'Toggle navigation');
        toggle.setAttribute('aria-controls', 'appSidebar');
    }
    if (!sidebar.id) sidebar.id = 'appSidebar';
    sidebar.setAttribute('aria-label', 'Main navigation');

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') closeMobileSidebar();
    });
    setToggleExpanded();
});
