/* ============================================================
   Sidebar active link — highlight on scroll
   ============================================================ */
const sections = document.querySelectorAll('section[id]');
const navLinks = document.querySelectorAll('.nav-link');

function setActive(id) {
  navLinks.forEach(link => {
    link.classList.toggle('active', link.getAttribute('href') === `#${id}`);
  });
}

const observer = new IntersectionObserver(
  entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) setActive(entry.target.id);
    });
  },
  { rootMargin: '-20% 0px -70% 0px', threshold: 0 }
);

sections.forEach(s => observer.observe(s));

/* ============================================================
   Tabs
   ============================================================ */
document.querySelectorAll('.tab-group').forEach(group => {
  group.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      const targetId = tab.dataset.tab;

      // Deactivate all tabs in this group
      group.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      // Find the sibling tab-content blocks — walk up to the shared parent
      const parent = group.parentElement;
      parent.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === targetId);
      });
    });
  });
});
