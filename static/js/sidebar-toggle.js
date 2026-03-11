// Sidebar toggle functionality
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('collapsed');

    // Save state to localStorage
    const isCollapsed = sidebar.classList.contains('collapsed');
    localStorage.setItem('sidebarCollapsed', isCollapsed);
}

// Restore sidebar state on page load
document.addEventListener('DOMContentLoaded', function () {
    const sidebar = document.querySelector('.sidebar');
    const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';

    if (isCollapsed) {
        sidebar.classList.add('collapsed');
    }
});
