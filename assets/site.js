'use strict';
// Progressive enhancement: the full publication record remains visible without JS.
const tools = document.querySelector('.publication-tools');
if (tools) {
  tools.hidden = false;
  const buttons = [...tools.querySelectorAll('[data-filter]')];
  const papers = [...document.querySelectorAll('.publication')];
  const search = document.getElementById('paper-search');
  const count = document.getElementById('pub-count');
  const empty = document.getElementById('empty-state');
  let topic = 'all';
  function update() {
    const words = search.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
    let visible = 0;
    for (const paper of papers) {
      const matches = (topic === 'all' || paper.dataset.topic === topic) && words.every(word => paper.dataset.search.includes(word));
      paper.hidden = !matches;
      if (matches) visible++;
    }
    const template = visible === papers.length ? count.dataset.allTemplate : count.dataset.filteredTemplate;
    count.textContent = template.replace('{n}', String(visible)).replace('{total}', String(papers.length));
    empty.hidden = visible > 0;
  }
  for (const button of buttons) {
    button.addEventListener('click', () => {
      topic = button.dataset.filter;
      for (const item of buttons) {
        const active = item === button;
        item.classList.toggle('selected', active);
        item.setAttribute('aria-pressed', String(active));
      }
      update();
    });
  }
  search.addEventListener('input', update);
}
const language = document.getElementById('cv-language');
if (language) language.addEventListener('change', () => {
  const code = language.value === 'Zh' ? 'Zh' : 'En';
  const preview = document.getElementById('cv-preview');
  preview.src = `/pdf/${code}_resume.pdf#view=FitH`;
  preview.title = code === 'Zh' ? preview.dataset.titleZh : preview.dataset.titleEn;
});
// Keep the current section on explicit language switches; never redirect by locale.
const languageSwitch = document.querySelector('.language-switch');
if (languageSwitch) languageSwitch.addEventListener('click', () => {
  const destination = new URL(languageSwitch.href);
  destination.hash = window.location.hash;
  languageSwitch.href = destination.href;
});
