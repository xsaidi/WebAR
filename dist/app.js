'use strict';
const photoViews = {
  angle: {name: 'под углом', index: '01', alt: 'Терракотовый диван Форма с двумя подушками сиденья и прямыми металлическими ножками, ракурс под углом'},
  front: {name: 'спереди', index: '02', alt: 'Терракотовый диван Форма, вид строго спереди'},
  side: {name: 'сбоку', index: '03', alt: 'Терракотовый диван Форма, вид сбоку с прямым подлокотником'},
  back: {name: 'сзади', index: '04', alt: 'Терракотовый диван Форма, вид сзади с прямоугольной спинкой'}
};
document.querySelectorAll('.photo-view').forEach(button => {
  button.addEventListener('click', () => {
    const view = photoViews[button.dataset.view];
    const image = document.querySelector('#hero-sofa');
    image.src = `assets/sofa-${button.dataset.view}.webp`;
    image.alt = view.alt;
    document.querySelector('#view-index').textContent = `${view.index} / 04`;
    document.querySelector('#view-status').textContent = `Ракурс: ${view.name}`;
    document.querySelectorAll('.photo-view').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
  });
});
const colors = {
  terra: { name: 'Терракота', number: '01', fabric: '#ad5c40', light: '#c27b5b', dark: '#783d2c', description: 'Тёплый акцент для бетона, дерева и вечернего света.' },
  graphite: { name: 'Графит', number: '02', fabric: '#535450', light: '#777971', dark: '#353632', description: 'Сдержанная глубина для выразительного пространства.' },
  sand: { name: 'Песок', number: '03', fabric: '#bbaa8e', light: '#d6c9b0', dark: '#8a7c63', description: 'Мягкий природный оттенок, который добавляет света.' },
  olive: { name: 'Олива', number: '04', fabric: '#71735b', light: '#999b7b', dark: '#4c503c', description: 'Приглушённый зелёный в гармонии с деревом и камнем.' }
};
const sketch = document.querySelector('#sofa-sketch');
const dialog = document.querySelector('#viewer-dialog');
let selectedColor = 'terra';
document.querySelectorAll('input[name="color"]').forEach(input => {
  input.addEventListener('change', () => {
    selectedColor = input.value;
    const color = colors[selectedColor];
    for (const key of ['fabric', 'light', 'dark']) sketch.style.setProperty(key === 'fabric' ? '--fabric' : `--fabric-${key}`, color[key]);
    document.querySelector('#sketch-title').textContent = `Эскиз дивана, цвет ${color.name}`;
    document.querySelector('#color-name').textContent = color.name;
    document.querySelector('#color-number').textContent = `${color.number} / 04`;
    document.querySelector('#color-description').textContent = color.description;
  });
});
document.querySelector('#view-sofa').addEventListener('click', () => {
  document.querySelector('#dialog-color').textContent = colors[selectedColor].name;
  const mobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  document.querySelector('#dialog-description').textContent = mobile
    ? '3D-модель дивана ещё готовится. После её добавления на совместимом телефоне здесь можно будет разместить диван в комнате с помощью дополненной реальности.'
    : '3D-модель дивана ещё готовится. После её добавления здесь можно будет рассмотреть диван со всех сторон и выбрать цвет обивки.';
  dialog.showModal();
});
document.querySelectorAll('.close, .dialog-return').forEach(button => button.addEventListener('click', () => dialog.close()));
dialog.addEventListener('click', event => { if (event.target === dialog) { const rect = dialog.getBoundingClientRect(); if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close(); } });
