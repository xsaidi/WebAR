'use strict';
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
