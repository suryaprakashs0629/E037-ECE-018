document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-dismiss]').forEach(button => button.addEventListener('click', () => button.closest('.flash')?.remove()));
  document.querySelectorAll('form[data-confirm]').forEach(form => form.addEventListener('submit', event => {
    const message = form.getAttribute('data-confirm') || 'Continue?';
    if (!window.confirm(message)) event.preventDefault();
  }));
  document.querySelector('[data-sidebar-toggle]')?.addEventListener('click', () => {
    document.getElementById('sidebar')?.classList.toggle('open');
  });
  document.addEventListener('click', event => {
    const sidebar = document.getElementById('sidebar');
    if (sidebar && sidebar.classList.contains('open') && !sidebar.contains(event.target) && !event.target.closest('[data-sidebar-toggle]')) {
      sidebar.classList.remove('open');
    }
  });
  // Keep the time-window form legible and prevent accidental end-before-start selection.
  const start = document.querySelector('[name="start_slot"]');
  const end = document.querySelector('[name="end_slot"]');
  if (start && end) {
    start.addEventListener('change', () => {
      const s = Number(start.value);
      [...end.options].forEach(option => { option.disabled = Number(option.value) < s; });
      if (Number(end.value) < s) end.value = String(s);
    });
    start.dispatchEvent(new Event('change'));
  }
});
