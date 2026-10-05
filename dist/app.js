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
function setColor(key) {
  if (!colors[key]) return;
  selectedColor = key;
  const color = colors[key];
  for (const name of ['fabric', 'light', 'dark']) sketch.style.setProperty(name === 'fabric' ? '--fabric' : `--fabric-${name}`, color[name]);
  document.querySelector('#sketch-title').textContent = `Эскиз дивана, цвет ${color.name}`;
  document.querySelector('#color-name').textContent = color.name;
  document.querySelector('#color-number').textContent = `${color.number} / 04`;
  document.querySelector('#color-description').textContent = color.description;
  document.querySelector('#dialog-color').textContent = color.name;
  document.querySelectorAll('input[name="color"]').forEach(input => { input.checked = input.value === key; });
  document.querySelectorAll('[data-model-color]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.modelColor === key)));
}
document.querySelectorAll('input[name="color"]').forEach(input => {
  input.addEventListener('change', () => setColor(input.value));
});

// Load the entire rendering library only after the visitor asks to view the sofa.
let libraryPromise = null;
let libraryAttempts = 0;
async function loadViewerLibrary() {
  if (!libraryPromise) {
    libraryPromise = (async () => {
      // This preference is read before creating the shared WebGL renderer.
      window.ModelViewerElement = { powerPreference: 'low-power' };
      const attempt = libraryAttempts++;
      await import(`./vendor/model-viewer-4.3.1.min.js${attempt ? `?retry=${attempt}` : ''}`);
      await customElements.whenDefined('model-viewer');
      const Viewer = customElements.get('model-viewer');
      Viewer.modelCacheSize = 0;
      Viewer.minimumRenderScale = 0.5;
      return Viewer;
    })().catch(error => { libraryPromise = null; throw error; });
  }
  return libraryPromise;
}
const mount = document.querySelector('#viewer-mount');
const status = document.querySelector('#model-status');
const arButton = document.querySelector('#place-sofa');
const retryButton = document.querySelector('#retry-model');
const arHelp = document.querySelector('#ar-help');
const resetButton = document.querySelector('#reset-view');
let viewer = null;
let generation = 0;
let loadTimer = null;
let colorTimer = null;
let supportTimer = null;
let arLaunching = false;
let webxrSession = false;
const phoneLike = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);

function showStatus(text) { status.textContent = text; status.hidden = !text; }
function supportMessage() {
  if (!window.isSecureContext) return 'Для AR откройте опубликованную страницу по HTTPS. Просмотр в 3D доступен здесь.';
  if (window.self !== window.top) return 'Для AR откройте сайт отдельной вкладкой: Safari на iPhone или Chrome на Android.';
  if (phoneLike) return 'AR недоступна в этом браузере или на устройстве. Откройте сайт в Safari на iPhone или Chrome на Android. Для Android нужна поддержка ARCore и Google Play Services для AR.';
  return 'Чтобы поставить диван в комнате, откройте эту страницу на телефоне: Safari на iPhone или Chrome на Android с поддержкой AR.';
}
function refreshAR() {
  const ready = !!viewer?.loaded && mount.getAttribute('aria-busy') === 'false';
  const supported = ready && viewer.canActivateAR && window.isSecureContext;
  arButton.hidden = !supported;
  arButton.disabled = !supported || arLaunching;
  resetButton.disabled = !ready;
  arHelp.textContent = supported
    ? 'Выберите цвет, затем нажмите «Поставить в комнате». Наведите камеру на освещённый свободный участок пола.'
    : ready ? supportMessage() : 'Проверяем возможность AR после загрузки модели…';
}
// Capability detection can finish after the GLB loads; probe briefly, then stop.
function checkARSupport() {
  clearTimeout(supportTimer);
  let remaining = 20;
  const check = () => {
    if (!dialog.open || !viewer || webxrSession) return;
    refreshAR();
    if (!viewer.canActivateAR && --remaining > 0) supportTimer = setTimeout(check, 200);
  };
  check();
}
function finishLoading() {
  clearTimeout(loadTimer);
  mount.setAttribute('aria-busy', 'false');
  retryButton.hidden = true;
  showStatus('');
  checkARSupport();
}
function failViewing(message) {
  clearTimeout(loadTimer);
  mount.setAttribute('aria-busy', 'false');
  showStatus(message);
  retryButton.hidden = false;
  arButton.hidden = true;
  resetButton.disabled = true;
  arHelp.textContent = 'Можно повторить загрузку или вернуться к фотографиям дивана.';
}
function startLoading() {
  clearTimeout(loadTimer);
  clearTimeout(supportTimer);
  mount.setAttribute('aria-busy', 'true');
  showStatus('Загружаем 3D-модель…');
  retryButton.hidden = true;
  arButton.hidden = true;
  resetButton.disabled = true;
  loadTimer = setTimeout(() => {
    if (dialog.open && mount.getAttribute('aria-busy') === 'true') {
      showStatus('Загрузка занимает больше времени. Проверьте соединение или повторите попытку.');
      retryButton.hidden = false;
    }
  }, 25000);
}
function modelPath(key) { return `assets/models/sofa-${key}.glb`; }
function clearViewer() {
  generation++;
  clearTimeout(loadTimer);
  clearTimeout(colorTimer);
  clearTimeout(supportTimer);
  if (viewer) {
    viewer.src = null;
    viewer.remove();
    viewer = null;
  }
  mount.replaceChildren();
  arLaunching = false;
  webxrSession = false;
}
async function createViewer() {
  clearViewer();
  const token = generation;
  startLoading();
  const poster = document.createElement('img');
  poster.src = 'assets/sofa-poster.webp';
  poster.alt = 'Диван Форма — предпросмотр';
  poster.className = 'viewer-poster';
  mount.append(poster);
  try {
    await loadViewerLibrary();
    if (!dialog.open || token !== generation) return;
    const element = document.createElement('model-viewer');
    viewer = element;
    element.setAttribute('alt', `Диван Форма, ${colors[selectedColor].name}. Интерактивная 3D-модель.`);
    element.setAttribute('camera-controls', '');
    element.setAttribute('touch-action', 'pan-y');
    element.setAttribute('camera-orbit', '25deg 72deg auto');
    element.setAttribute('min-camera-orbit', 'auto 10deg 70%');
    element.setAttribute('max-camera-orbit', 'auto 90deg 220%');
    element.setAttribute('field-of-view', '30deg');
    element.setAttribute('shadow-intensity', '0');
    element.setAttribute('interaction-prompt', 'none');
    element.setAttribute('loading', 'eager');
    element.setAttribute('poster', 'assets/sofa-poster.webp');
    element.setAttribute('ar', '');
    // Private asset URLs cannot be fetched by Android's separate Scene Viewer app.
    // WebXR keeps authenticated loading in the browser; iOS creates a local USDZ blob.
    element.setAttribute('ar-modes', 'webxr quick-look');
    element.setAttribute('ar-placement', 'floor');
    element.setAttribute('ar-scale', 'fixed');
    element.setAttribute('ar-usdz-max-texture-size', '512');
    // Use our accessible external AR control instead of the component's default button.
    const hiddenAR = document.createElement('span');
    hiddenAR.slot = 'ar-button'; hiddenAR.hidden = true; element.append(hiddenAR);
    const xrClose = document.createElement('button');
    xrClose.slot = 'exit-webxr-ar-button'; xrClose.type = 'button'; xrClose.className = 'xr-close';
    xrClose.textContent = 'Вернуться к 3D'; element.append(xrClose);
    const xrHelp = document.createElement('p');
    xrHelp.className = 'xr-prompt';
    xrHelp.textContent = 'Медленно направьте телефон на пол и коснитесь экрана для размещения.';
    element.append(xrHelp);
    element.addEventListener('progress', event => {
      if (viewer !== element || arLaunching) return;
      if (mount.getAttribute('aria-busy') === 'true') showStatus(`Загружаем 3D-модель… ${Math.round(event.detail.totalProgress * 100)}%`);
    });
    element.addEventListener('load', () => {
      if (viewer !== element) return;
      if (element.src !== modelPath(selectedColor)) return;
      finishLoading();
    });
    element.addEventListener('error', () => {
      if (viewer === element) failViewing('Не удалось открыть 3D-модель. Проверьте соединение или попробуйте другой браузер.');
    });
    element.addEventListener('ar-status', event => {
      if (viewer !== element) return;
      const state = event.detail.status;
      if (state === 'failed') {
        webxrSession = false; arLaunching = false; refreshAR();
        dialog.classList.remove('in-ar');
        arHelp.textContent = 'AR не удалось запустить. Проверьте разрешение камеры и поддержку AR на устройстве. Встроенный браузер мессенджера замените на Safari или Chrome.';
      } else if (state === 'session-started' || state === 'object-placed') {
        webxrSession = true;
        dialog.classList.add('in-ar');
        xrHelp.hidden = state === 'object-placed';
      } else if (state === 'not-presenting') {
        webxrSession = false; arLaunching = false;
        dialog.classList.remove('in-ar'); refreshAR();
      }
    });
    // A new URL for every color preserves that color in both WebXR and Quick Look.
    element.src = modelPath(selectedColor);
    mount.replaceChildren(element);
  } catch (error) {
    if (dialog.open && token === generation) failViewing('Просмотр не загрузился. Проверьте соединение и попробуйте снова.');
  }
}
document.querySelector('#view-sofa').addEventListener('click', () => {
  setColor(selectedColor);
  dialog.showModal();
  createViewer();
});
document.querySelectorAll('[data-model-color]').forEach(button => button.addEventListener('click', () => {
  const key = button.dataset.modelColor;
  if (key === selectedColor) return;
  setColor(key);
  if (!viewer) return;
  startLoading();
  clearTimeout(colorTimer);
  colorTimer = setTimeout(() => {
    if (!viewer || !dialog.open) return;
    viewer.alt = `Диван Форма, ${colors[selectedColor].name}. Интерактивная 3D-модель.`;
    const target = modelPath(selectedColor);
    if (viewer.src === target && viewer.loaded) finishLoading();
    else viewer.src = target;
  }, 160);
}));
arButton.addEventListener('click', () => {
  if (!viewer?.loaded || !viewer.canActivateAR || arLaunching) return;
  arLaunching = true; arButton.disabled = true;
  arHelp.textContent = 'Подготавливаем AR. На iPhone откроется системный просмотр: выберите вкладку AR.';
  // Do not await network/import here: Quick Look must start from the user gesture.
  viewer.activateAR().catch(() => {
    arHelp.textContent = 'Не удалось запустить AR. Откройте страницу в Safari на iPhone или Chrome на Android и разрешите доступ к камере.';
  }).finally(() => {
    arLaunching = false;
    if (viewer && dialog.open && !webxrSession) { arButton.disabled = false; }
  });
});
resetButton.addEventListener('click', () => {
  if (!viewer) return;
  viewer.cameraOrbit = '25deg 72deg auto';
  viewer.fieldOfView = '30deg';
});
retryButton.addEventListener('click', createViewer);
document.querySelector('.close').addEventListener('click', () => { if (!webxrSession) dialog.close(); });
document.querySelector('#viewer-back').addEventListener('click', () => dialog.close());
dialog.addEventListener('close', () => { clearViewer(); dialog.classList.remove('in-ar'); });
dialog.addEventListener('cancel', event => { if (webxrSession) event.preventDefault(); });
dialog.addEventListener('click', event => {
  if (event.target !== dialog || webxrSession) return;
  const rect = dialog.getBoundingClientRect();
  if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
});
window.addEventListener('pageshow', () => { if (dialog.open && viewer) checkARSupport(); });
document.addEventListener('visibilitychange', () => {
  if (!document.hidden && dialog.open && viewer && !webxrSession) checkARSupport();
});
