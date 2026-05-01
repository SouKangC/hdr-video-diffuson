// user_study/HDR_Video_Project_Page/js/ev-gallery.js
//
// Declarative EV gallery: a single <img> swapped on (scene, method, ev) input.
// Container element configures everything via data-* attributes; this module
// has no hardcoded scene IDs, method names, or paths.
//
// Required container attributes:
//   data-scenes-src      URL to scenes.json (array of {id, label, ...})
//   data-methods         JSON array of method labels
//   data-evs             JSON array of integer EV stops
//   data-template        URL template using {scene}, {method}, {ev} placeholders
//
// Optional fallback:
//   data-scenes-fallback inline JSON used when fetch fails (e.g. file:// previews)

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

  const state = {
    sceneIdx: 0,
    methodIdx: methods.indexOf("Ours") >= 0 ? methods.indexOf("Ours") : 0,
    ev: 0,
  };

  const sceneRow = root.querySelector(".scene-row");
  const methodRow = root.querySelector(".method-row");
  const img = root.querySelector(".gallery-img");
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

  // Build method tabs.
  methods.forEach((m, i) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "button is-small is-rounded";
    b.textContent = m;
    b.dataset.idx = String(i);
    b.addEventListener("click", () => { state.methodIdx = i; render(); });
    methodRow.appendChild(b);
  });

  // Wire slider.
  slider.min = String(Math.min(...evs));
  slider.max = String(Math.max(...evs));
  slider.step = "1";
  slider.value = "0";
  slider.addEventListener("input", () => {
    state.ev = parseInt(slider.value, 10);
    render();
  });

  // Helper: set <img> src and update active classes.
  const preloadCache = new Map();
  function urlFor(sceneIdx, methodIdx, ev) {
    return buildTileUrl(template, {
      scene: scenes[sceneIdx].id,
      method: methods[methodIdx],
      ev,
    });
  }
  function preload(url) {
    if (preloadCache.has(url)) return;
    const im = new Image();
    im.src = url;
    preloadCache.set(url, im);
    if (preloadCache.size > 64) {
      // bounded LRU-ish: drop the oldest entry
      const firstKey = preloadCache.keys().next().value;
      preloadCache.delete(firstKey);
    }
  }
  function render() {
    img.src = urlFor(state.sceneIdx, state.methodIdx, state.ev);
    evLabel.textContent = formatEv(state.ev);
    [...sceneRow.children].forEach((b, i) =>
      b.classList.toggle("is-active-tab", i === state.sceneIdx));
    [...methodRow.children].forEach((b, i) =>
      b.classList.toggle("is-active-tab", i === state.methodIdx));

    // Preload neighbors.
    const evNeighbors = [state.ev - 1, state.ev + 1].filter(e =>
      e >= Math.min(...evs) && e <= Math.max(...evs));
    evNeighbors.forEach(e => preload(urlFor(state.sceneIdx, state.methodIdx, e)));
    [state.methodIdx - 1, state.methodIdx + 1]
      .filter(i => i >= 0 && i < methods.length)
      .forEach(i => preload(urlFor(state.sceneIdx, i, state.ev)));
    [state.sceneIdx - 1, state.sceneIdx + 1]
      .filter(i => i >= 0 && i < scenes.length)
      .forEach(i => preload(urlFor(i, state.methodIdx, state.ev)));
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
