// user_study/HDR_Video_Project_Page/js/ev-gallery.js
//
// Declarative EV gallery: a grid of method panels that all swap in lock-step on
// (scene, ev) input. Container element configures everything via data-*
// attributes; this module has no hardcoded scene IDs, method names, or paths.
//
// Required container attributes:
//   data-scenes-src      URL to scenes.json (array of {id, label, ...})
//   data-methods         JSON array of method labels (one panel per method)
//   data-evs             JSON array of integer EV stops
//   data-template        URL template using {scene}, {method}, {ev} placeholders
//
// Optional fallback:
//   data-scenes-fallback inline JSON used when fetch fails (e.g. file:// previews)
//
// Required child elements:
//   .scene-row       container for scene-tab buttons (filled by JS)
//   .gallery-grid    container for one panel per method (filled by JS)
//   .ev-slider       <input type="range"> driving EV stop
//   .ev-label .ev    span receiving the formatted EV string

export function formatEv(ev) {
  // "+0", "+3", "-2" — matches the convention used by the render script.
  return ev >= 0 ? `+${ev}` : `${ev}`;
}

export function buildTileUrl(template, { scene, method, ev }) {
  return template
    .replace("{scene}", String(scene))
    .replace("{method}", String(method))
    .replace("{ev}", formatEv(ev));
}

// Browser-only init below; guarded so Node tests can import the helpers.
if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".ev-gallery").forEach(initGallery);
  });
}

async function initGallery(root) {
  const methods = JSON.parse(root.dataset.methods);
  const evs = JSON.parse(root.dataset.evs);
  const template = root.dataset.template;
  const scenes = await loadScenes(root);

  if (!scenes.length) {
    console.error("ev-gallery: no scenes available");
    return;
  }

  const state = { sceneIdx: 0, ev: 0 };

  const sceneRow = root.querySelector(".scene-row");
  const grid = root.querySelector(".gallery-grid");
  const slider = root.querySelector(".ev-slider");
  const evLabel = root.querySelector(".ev-label .ev");

  // Build scene tabs.
  scenes.forEach((s, i) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "button is-small is-rounded";
    b.textContent = `Scene ${s.label}`;
    b.dataset.idx = String(i);
    b.addEventListener("click", () => { state.sceneIdx = i; render(); });
    sceneRow.appendChild(b);
  });

  // Build one panel per method. Each panel = label + image. Clicking a panel
  // opens the zoom modal locked to that method (kept in sync as scene/EV change).
  const panelImgs = [];
  methods.forEach((m, i) => {
    const panel = document.createElement("div");
    panel.className = "gallery-panel" + (m === "Ours" ? " is-ours" : "");
    const label = document.createElement("div");
    label.className = "panel-label";
    label.textContent = m;
    const im = document.createElement("img");
    im.className = "panel-img";
    im.alt = `${m} reconstruction`;
    im.loading = "lazy";
    im.addEventListener("click", () => openZoom(i));
    panel.appendChild(label);
    panel.appendChild(im);
    grid.appendChild(panel);
    panelImgs.push(im);
  });

  // Modal wiring.
  const modal = root.querySelector(".panel-zoom-modal");
  const zoomImg = modal && modal.querySelector(".zoom-img");
  const zoomLabel = modal && modal.querySelector(".zoom-label");
  const zoomState = { open: false, methodIdx: 0 };

  function openZoom(methodIdx) {
    if (!modal) return;
    zoomState.open = true;
    zoomState.methodIdx = methodIdx;
    syncZoom();
    modal.classList.add("is-active");
  }
  function closeZoom() {
    if (!modal) return;
    zoomState.open = false;
    modal.classList.remove("is-active");
  }
  function syncZoom() {
    if (!modal || !zoomState.open) return;
    const m = methods[zoomState.methodIdx];
    zoomImg.src = urlFor(state.sceneIdx, m, state.ev);
    zoomImg.alt = `${m} — Scene ${scenes[state.sceneIdx].label}, EV ${formatEv(state.ev)}`;
    zoomLabel.textContent =
      `${m}  ·  Scene ${scenes[state.sceneIdx].label}  ·  EV ${formatEv(state.ev)}`;
  }
  if (modal) {
    modal.querySelector(".modal-background").addEventListener("click", closeZoom);
    modal.querySelector(".modal-close").addEventListener("click", closeZoom);
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && zoomState.open) closeZoom();
    });
  }

  // Wire slider.
  slider.min = String(Math.min(...evs));
  slider.max = String(Math.max(...evs));
  slider.step = "1";
  slider.value = "0";
  slider.addEventListener("input", () => {
    state.ev = parseInt(slider.value, 10);
    render();
  });

  // Image preload cache (bounded LRU-ish).
  const preloadCache = new Map();
  function urlFor(sceneIdx, methodLabel, ev) {
    return buildTileUrl(template, {
      scene: scenes[sceneIdx].id,
      method: methodLabel,
      ev,
    });
  }
  function preload(url) {
    if (preloadCache.has(url)) return;
    const im = new Image();
    im.src = url;
    preloadCache.set(url, im);
    if (preloadCache.size > 128) {
      const firstKey = preloadCache.keys().next().value;
      preloadCache.delete(firstKey);
    }
  }
  function render() {
    methods.forEach((m, i) => {
      panelImgs[i].src = urlFor(state.sceneIdx, m, state.ev);
    });
    evLabel.textContent = formatEv(state.ev);
    [...sceneRow.children].forEach((b, i) =>
      b.classList.toggle("is-active-tab", i === state.sceneIdx));
    syncZoom();

    // Preload all methods at adjacent EV ticks, and the current EV at adjacent scenes.
    const minEv = Math.min(...evs);
    const maxEv = Math.max(...evs);
    [state.ev - 1, state.ev + 1]
      .filter(e => e >= minEv && e <= maxEv)
      .forEach(e => methods.forEach(m => preload(urlFor(state.sceneIdx, m, e))));
    [state.sceneIdx - 1, state.sceneIdx + 1]
      .filter(i => i >= 0 && i < scenes.length)
      .forEach(i => methods.forEach(m => preload(urlFor(i, m, state.ev))));
  }

  render();
}

async function loadScenes(root) {
  const src = root.dataset.scenesSrc;
  if (src) {
    try {
      const r = await fetch(src);
      if (r.ok) return await r.json();
    } catch (e) {
      console.warn("ev-gallery: scenes fetch failed, using fallback", e);
    }
  }
  if (root.dataset.scenesFallback) {
    return JSON.parse(root.dataset.scenesFallback);
  }
  return [];
}
