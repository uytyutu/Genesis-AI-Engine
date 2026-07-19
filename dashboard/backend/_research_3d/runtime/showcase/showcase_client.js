/**
 * Universal Showcase Library client — niche from ?niche= / data-niche.
 * Never hardcodes dental. Empty stage forbidden (preview / css fallback).
 */
const LOAD_TIMEOUT_MS = 12000;
const HDR_PATH = "../hdr/";
const HDR_FILE = "studio_small.hdr";
const LIBRARY_URL = "../../showcases/library.json";
const PRODUCTS_URL = "../../showcases/products_manifest.json";

const els = {
  badge: document.getElementById("mode-badge"),
  loading: document.getElementById("showcase-loading"),
  loadingText: document.getElementById("showcase-loading-text"),
  still: document.getElementById("showcase-still"),
  canvasWrap: document.getElementById("showcase-canvas-wrap"),
  hint: document.getElementById("showcase-hint"),
  title: document.getElementById("showcase-title"),
  sub: document.getElementById("showcase-sub"),
  kicker: document.getElementById("showcase-kicker"),
  stage: document.getElementById("showcase-stage"),
  root: document.querySelector("[data-showcase-root]"),
  nicheSelect: document.getElementById("niche-select"),
  aliasHint: document.getElementById("alias-hint"),
  upgradeBtn: document.getElementById("upgrade-premium"),
  hotspots: document.getElementById("vxp-hotspots"),
};

let currentNiche = "generic";
let currentTier = "premium";
let qualityMeta = {
  quality: "placeholder",
  client_facing_3d: false,
  label_de: "Premium Showcase",
  label_en: "Premium Showcase",
  sub_de: "Digitale Präsentation moderner Technologien.",
};
let previewUrl = "";
let modelUrlRel = "";
let threeSession = null;
let library = { niches: [], aliases: {} };
let productsManifest = { products: [] };

function specializationFromUrl() {
  return new URLSearchParams(location.search).get("specialization") || "";
}

function scoreProductRow(row, specialization, tier) {
  let total = Number(row.score || 50);
  const spec = String(specialization || "").toLowerCase().replace(/[-\s]+/g, "_");
  const tokens = new Set(spec.split(/[^\w]+/).filter((t) => t.length >= 3));
  const specs = (row.specializations || []).map((s) => String(s).toLowerCase());
  if (specs.some((s) => tokens.has(s) || spec.includes(s))) total += 40;
  if (row.premium && tier === "premium") total += 6;
  return total;
}

async function pickProductForNiche(niche, specialization, tier) {
  const rows = (productsManifest.products || []).filter((p) => p.niche_id === niche);
  if (!rows.length) return null;
  const forced = new URLSearchParams(location.search).get("product");
  if (forced && rows.some((r) => r.product_id === forced)) {
    return rows.find((r) => r.product_id === forced);
  }
  rows.sort(
    (a, b) =>
      scoreProductRow(b, specialization, tier) - scoreProductRow(a, specialization, tier)
  );
  return rows[0];
}

function setBadge(msg) {
  if (els.badge) els.badge.textContent = msg;
}

function setUpsellVisible(show) {
  if (!els.upgradeBtn) return;
  els.upgradeBtn.hidden = !show;
}

function renderHotspots(chips) {
  if (!els.hotspots) return;
  els.hotspots.innerHTML = "";
  const list = (chips || []).slice(0, 4);
  if (!list.length) {
    els.hotspots.hidden = true;
    return;
  }
  els.hotspots.hidden = false;
  for (const h of list) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "hotspot-chip";
    btn.textContent = h.label_de || h.label_en || h.id || "Info";
    btn.addEventListener("click", () => {
      els.hotspots.querySelectorAll(".hotspot-chip").forEach((c) =>
        c.classList.remove("is-active")
      );
      btn.classList.add("is-active");
      if (els.hint) {
        els.hint.textContent =
          (h.label_de || h.label_en || "") +
          (h.action ? " · " + h.action : "");
      }
    });
    els.hotspots.appendChild(btn);
  }
}

async function loadSpecHotspots(niche) {
  try {
    const res = await fetch("../../showcases/specialization_map.json");
    if (!res.ok) return;
    const map = await res.json();
    const specs = map.specializations || {};
    const specialization = specializationFromUrl();
    let row = null;
    const key = String(specialization || "").toLowerCase().replace(/\s+/g, "_");
    if (key && specs[key]) row = specs[key];
    if (!row) {
      row = Object.values(specs).find((r) => r && r.niche === niche) || null;
    }
    if (!row) row = specs.general || null;
    renderHotspots((row && row.hotspots) || []);
  } catch {
    renderHotspots([]);
  }
}

function withTimeout(promise, ms, label) {
  return Promise.race([
    promise,
    new Promise((_, reject) =>
      setTimeout(() => reject(new Error(label + " timeout " + ms + "ms")), ms)
    ),
  ]);
}

function nicheFromUrl() {
  const q = new URLSearchParams(location.search).get("niche");
  if (q) return q.trim().toLowerCase();
  return (document.body.dataset.niche || "generic").toLowerCase();
}

function tierFromUrl() {
  const t = new URLSearchParams(location.search).get("tier");
  if (t === "basic" || t === "business" || t === "premium") return t;
  return "premium";
}

function canonicalizeNiche(raw) {
  const key = String(raw || "generic").toLowerCase();
  const aliases = library.aliases || {};
  return aliases[key] || key;
}

function showcaseBase(niche) {
  return `../../showcases/${niche}/`;
}

async function resolvePreviewUrl(niche, preferred) {
  const base = showcaseBase(niche);
  const candidates = [
    preferred,
    "preview.webp",
    "preview.jpg",
    "preview.png",
  ].filter(Boolean);
  for (const name of candidates) {
    const url = base + name + (name.includes("?") ? "" : "?v=lib1");
    try {
      const res = await fetch(url, { method: "HEAD" });
      if (res.ok) return url;
    } catch {
      /* try next */
    }
  }
  // GET fallback (some servers lack HEAD)
  for (const name of ["preview.jpg", "preview.webp", preferred].filter(Boolean)) {
    const url = base + name + "?v=lib1";
    try {
      const res = await fetch(url);
      if (res.ok) return url;
    } catch {
      /* */
    }
  }
  return "";
}

function applyTierChrome(tier) {
  currentTier = tier;
  document.body.dataset.tier = tier;
  document.querySelectorAll("#tier-switch button").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tier === tier);
  });
  const url = new URL(location.href);
  url.searchParams.set("tier", tier);
  url.searchParams.set("niche", currentNiche);
  history.replaceState({}, "", url);
}

function showPreview(reason) {
  if (els.still && previewUrl) {
    els.still.hidden = false;
    els.still.style.backgroundImage = `url("${previewUrl}")`;
    els.still.classList.add("is-visible");
    els.still.classList.remove("is-dimmed", "is-faded");
  }
  if (els.loading) {
    els.loading.hidden = true;
    els.loading.style.display = "none";
  }
  if (els.canvasWrap) {
    els.canvasWrap.hidden = true;
    els.canvasWrap.classList.remove("is-visible");
  }
  if (els.hint && reason) els.hint.textContent = reason;
}

function hideLoading() {
  if (els.loading) {
    els.loading.hidden = true;
    els.loading.style.display = "none";
  }
}

function showLoading() {
  if (els.loading) {
    els.loading.hidden = false;
    els.loading.style.display = "";
  }
}

function disposeThree() {
  if (threeSession) {
    threeSession.dispose();
    threeSession = null;
  }
  if (els.canvasWrap) {
    els.canvasWrap.innerHTML = "";
    els.canvasWrap.hidden = true;
    els.canvasWrap.classList.remove("is-visible");
  }
}

function allowsInteractive3d() {
  if (new URLSearchParams(location.search).get("lab3d") === "1") return true;
  const q = String(qualityMeta.quality || "").toLowerCase();
  return (
    qualityMeta.client_facing_3d === true &&
    (q === "approved" || q === "premium")
  );
}

async function loadQuality(niche) {
  const base = showcaseBase(niche);
  const specialization = specializationFromUrl();
  const picked = await pickProductForNiche(niche, specialization, currentTier);
  let productBase = base;
  if (picked) {
    productBase = base + "products/" + picked.product_id + "/";
  }

  try {
    const res = await fetch(base + "quality.json");
    if (!res.ok) throw new Error("quality.json HTTP " + res.status);
    qualityMeta = await res.json();
  } catch (e) {
    console.warn("[vxp] quality", niche, e);
    qualityMeta = {
      quality: "placeholder",
      client_facing_3d: false,
      label_de: niche,
      label_en: niche,
      sub_de: "Visual Experience für diese Branche wird vorbereitet.",
    };
  }

  if (picked) {
    try {
      const pr = await fetch(productBase + "product.json");
      if (pr.ok) {
        const prod = await pr.json();
        if (prod.label_de) qualityMeta.label_de = prod.label_de;
        if (prod.label_en) qualityMeta.label_en = prod.label_en;
        if (prod.quality) qualityMeta.quality = prod.quality;
        if (prod.client_facing_3d != null) {
          qualityMeta.client_facing_3d = prod.client_facing_3d;
        }
        qualityMeta.product_id = prod.id || picked.product_id;
        qualityMeta.product_score = prod.score;
      }
    } catch {
      /* optional */
    }
  }

  try {
    const metaRes = await fetch(base + "metadata.json");
    if (metaRes.ok) {
      const meta = await metaRes.json();
      if (meta.sub_de) qualityMeta.sub_de = meta.sub_de;
      if (meta.sub_en) qualityMeta.sub_en = meta.sub_en;
    }
  } catch {
    /* optional */
  }

  previewUrl =
    (await resolvePreviewUrlFromBase(productBase)) ||
    (await resolvePreviewUrl(niche, qualityMeta.preview));

  modelUrlRel = productBase + "model.glb?v=lib1";
  const nicheModel = base + "model.glb?v=lib1";
  try {
    const probe = await fetch(modelUrlRel, { method: "HEAD" });
    if (!probe.ok) modelUrlRel = nicheModel;
  } catch {
    modelUrlRel = nicheModel;
  }

  if (els.title) els.title.textContent = qualityMeta.label_de || niche;
  if (els.sub) {
    els.sub.textContent =
      qualityMeta.sub_de ||
      "Automatisch passende Visual Experience für Ihr Gewerbe.";
  }
  if (els.kicker) {
    const pid = qualityMeta.product_id || "default";
    els.kicker.textContent =
      "Visual Experience · " +
      niche +
      "/" +
      pid +
      " · score=" +
      (qualityMeta.product_score ?? "?") +
      " · quality=" +
      (qualityMeta.quality || "?");
  }
}

async function resolvePreviewUrlFromBase(base) {
  for (const name of ["preview.webp", "preview.jpg", "preview.png"]) {
    const url = base + name + "?v=lib1";
    try {
      const res = await fetch(url);
      if (res.ok) return url;
    } catch {
      /* */
    }
  }
  return "";
}

function frameObject(THREE, camera, controls, object, dim) {
  object.scale.setScalar(1);
  object.position.set(0, 0, 0);
  object.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(object);
  if (box.isEmpty()) return;
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const maxDim = Math.max(size.x, size.y, size.z, 0.001);
  const targetSize = 1.75;
  const scale = targetSize / maxDim;
  object.scale.setScalar(scale);
  object.position.set(0, 0, 0);
  object.position.sub(center.clone().multiplyScalar(scale));
  object.updateMatrixWorld(true);

  camera.aspect = dim.w / Math.max(dim.h, 1);
  const fov = (camera.fov * Math.PI) / 180;
  const halfFov = Math.tan(fov / 2);
  const distForHeight = (size.y * scale) / 2 / halfFov;
  const distForWidth =
    (size.x * scale) / 2 / (halfFov * Math.max(camera.aspect, 0.1));
  const dist = Math.max(distForHeight, distForWidth, targetSize * 0.9) * 2.35;

  camera.near = Math.max(dist / 100, 0.01);
  camera.far = Math.max(dist * 100, 100);
  camera.position.set(dist * 0.28, dist * 0.22, dist);
  camera.lookAt(0, 0, 0);
  camera.updateProjectionMatrix();
  if (controls) {
    controls.target.set(0, 0, 0);
    controls.minDistance = dist * 0.45;
    controls.maxDistance = dist * 5;
    controls.update();
  }
}

async function mountInteractive() {
  showLoading();
  if (els.still) {
    els.still.classList.add("is-visible", "is-dimmed");
  }

  const THREE = await withTimeout(import("three"), LOAD_TIMEOUT_MS, "three");
  const { GLTFLoader } = await withTimeout(
    import("three/addons/loaders/GLTFLoader.js"),
    LOAD_TIMEOUT_MS,
    "GLTFLoader"
  );
  const { OrbitControls } = await withTimeout(
    import("three/addons/controls/OrbitControls.js"),
    LOAD_TIMEOUT_MS,
    "OrbitControls"
  );

  const wrap = els.canvasWrap;
  wrap.hidden = false;
  wrap.innerHTML = "";
  await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));

  const w = Math.max(wrap.clientWidth || els.stage?.clientWidth || 0, 280);
  const h = Math.max(wrap.clientHeight || els.stage?.clientHeight || 0, 300);

  const scene = new THREE.Scene();
  scene.background = null;
  const camera = new THREE.PerspectiveCamera(40, w / h, 0.01, 100);
  camera.position.set(0, 0.4, 2.5);

  const renderer = new THREE.WebGLRenderer({
    antialias: true,
    alpha: true,
    premultipliedAlpha: false,
  });
  renderer.setClearColor(0x000000, 0);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(w, h, false);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.55;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  wrap.appendChild(renderer.domElement);

  scene.add(new THREE.HemisphereLight(0xf8fafc, 0x1e293b, 0.55));
  const key = new THREE.DirectionalLight(0xffffff, 1.35);
  key.position.set(2.8, 4.2, 3.2);
  scene.add(key);
  const fill = new THREE.DirectionalLight(0xe2e8f0, 0.45);
  fill.position.set(-2.2, 1.8, 1.5);
  scene.add(fill);
  const rim = new THREE.DirectionalLight(0x7dd3fc, 0.55);
  rim.position.set(-3.2, 1.2, -2.4);
  scene.add(rim);

  try {
    const { RGBELoader } = await import("three/addons/loaders/RGBELoader.js");
    const hdr = await withTimeout(
      new RGBELoader().setPath(HDR_PATH).loadAsync(HDR_FILE),
      5000,
      "HDR"
    );
    hdr.mapping = THREE.EquirectangularReflectionMapping;
    scene.environment = hdr;
  } catch (e) {
    console.warn("[showcase] HDR skipped", e);
  }

  const modelUrl = new URL(modelUrlRel, window.location.href).href;
  const probe = await fetch(modelUrl);
  if (!probe.ok) throw new Error("model.glb HTTP " + probe.status);
  const gltf = await withTimeout(
    new GLTFLoader().loadAsync(modelUrl),
    LOAD_TIMEOUT_MS,
    "GLTF"
  );
  const model = gltf.scene;
  model.traverse((obj) => {
    if (obj.isMesh && obj.material) {
      const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
      for (const m of mats) {
        if ("envMapIntensity" in m) m.envMapIntensity = 1.55;
        m.needsUpdate = true;
      }
    }
  });
  scene.add(model);

  frameObject(THREE, camera, null, model, { w, h });
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.enablePan = false;
  controls.autoRotate = true;
  controls.autoRotateSpeed = 0.55;
  frameObject(THREE, camera, controls, model, { w, h });

  let alive = true;
  const IDLE_RESUME_MS = 2800;
  let idleTimer = 0;
  const pause = () => {
    controls.autoRotate = false;
    window.clearTimeout(idleTimer);
  };
  const resume = () => {
    window.clearTimeout(idleTimer);
    idleTimer = window.setTimeout(() => {
      if (alive) controls.autoRotate = true;
    }, IDLE_RESUME_MS);
  };
  const canvasEl = renderer.domElement;
  canvasEl.addEventListener("pointerdown", pause);
  canvasEl.addEventListener("pointerup", resume);
  canvasEl.addEventListener("pointerleave", resume);
  canvasEl.addEventListener(
    "wheel",
    () => {
      pause();
      resume();
    },
    { passive: true }
  );

  renderer.render(scene, camera);
  function animate() {
    if (!alive) return;
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
  }
  animate();

  function onResize() {
    if (!alive) return;
    const nw = Math.max(wrap.clientWidth || 0, 280);
    const nh = Math.max(wrap.clientHeight || 0, 300);
    camera.aspect = nw / nh;
    camera.updateProjectionMatrix();
    renderer.setSize(nw, nh, false);
  }
  window.addEventListener("resize", onResize);
  hideLoading();
  wrap.classList.add("is-visible");
  if (els.still) els.still.classList.add("is-faded");

  threeSession = {
    dispose() {
      alive = false;
      window.clearTimeout(idleTimer);
      window.removeEventListener("resize", onResize);
      controls.dispose();
      renderer.dispose();
      wrap.innerHTML = "";
    },
  };
}

async function runShowcase(tier) {
  disposeThree();
  if (els.still) els.still.classList.remove("is-premium-still");

  if (tier === "basic") {
    if (els.root) els.root.style.opacity = "0.35";
    setUpsellVisible(false);
    showPreview("Basic: kein Visual-Experience-Block nötig.");
    setBadge("Basic");
    return;
  }
  if (els.root) els.root.style.opacity = "1";

  if (!previewUrl) {
    setUpsellVisible(false);
    showPreview("Visual Experience in Vorbereitung · Block bleibt sichtbar.");
    setBadge(tier + " · Platzhalter");
    if (els.still) {
      els.still.style.backgroundImage = "none";
      els.still.classList.add("is-visible");
      els.still.style.background =
        "radial-gradient(circle at 50% 45%, #334155, #0f172a 70%)";
    }
    return;
  }

  showPreview("");

  if (tier === "business") {
    // Visual Upselling: same object stays; Premium wakes it
    if (els.still) els.still.classList.add("is-premium-still");
    setUpsellVisible(true);
    showPreview(
      "Business: Preview · Upgrade to Premium — dasselbe Objekt wird lebendig."
    );
    setBadge("Business · Preview");
    return;
  }

  setUpsellVisible(false);

  if (!allowsInteractive3d()) {
    if (els.still) els.still.classList.add("is-premium-still");
    showPreview(
      "Premium · fotorealistisches Still · 3D nach quality=approved"
    );
    setBadge("Premium · digitale Präsentation");
    return;
  }

  try {
    await mountInteractive();
    setBadge(
      new URLSearchParams(location.search).get("lab3d") === "1"
        ? "Lab · 3D"
        : "Premium · 3D"
    );
    if (els.hint) {
      els.hint.textContent = "3D · drehen / zoomen · Glass-Stage";
    }
  } catch (e) {
    console.error(e);
    disposeThree();
    if (els.still) els.still.classList.add("is-premium-still");
    showPreview("3D-Fallback · Preview bleibt.");
    setBadge("Premium · Preview");
  }
}

async function applyNiche(nicheRaw, tier) {
  currentNiche = canonicalizeNiche(nicheRaw);
  document.body.dataset.niche = currentNiche;
  await loadQuality(currentNiche);
  await loadSpecHotspots(currentNiche);
  applyTierChrome(tier);
  await runShowcase(tier);
  if (els.aliasHint && library.aliases) {
    const requested = nicheFromUrl();
    if (requested !== currentNiche && library.aliases[requested]) {
      els.aliasHint.textContent =
        "alias " + requested + " → " + currentNiche;
    } else {
      els.aliasHint.textContent =
        "Visual Experience · Product Registry · never empty";
    }
  }
}

async function loadLibrary() {
  try {
    const res = await fetch(LIBRARY_URL);
    if (res.ok) library = await res.json();
  } catch {
    library = { niches: [], aliases: {} };
  }
  try {
    const res = await fetch(PRODUCTS_URL);
    if (res.ok) productsManifest = await res.json();
  } catch {
    productsManifest = { products: [] };
  }
  if (!els.nicheSelect) return;
  const list = library.niches || [];
  els.nicheSelect.innerHTML = "";
  for (const row of list) {
    const opt = document.createElement("option");
    opt.value = row.niche_id;
    const count = row.product_count || (row.products || []).length || 0;
    opt.textContent =
      (row.label_de || row.niche_id) + (count ? " · " + count + " products" : "");
    els.nicheSelect.appendChild(opt);
  }
  for (const [alias, target] of Object.entries(library.aliases || {})) {
    if (list.some((n) => n.niche_id === alias)) continue;
    const opt = document.createElement("option");
    opt.value = alias;
    opt.textContent = alias + " → " + target;
    els.nicheSelect.appendChild(opt);
  }
  els.nicheSelect.value = canonicalizeNiche(nicheFromUrl());
  els.nicheSelect.addEventListener("change", () => {
    applyNiche(els.nicheSelect.value, currentTier);
  });
}

async function boot() {
  await loadLibrary();
  document.querySelectorAll("#tier-switch button").forEach((btn) => {
    btn.addEventListener("click", () =>
      applyNiche(currentNiche, btn.dataset.tier)
    );
  });
  if (els.upgradeBtn) {
    els.upgradeBtn.addEventListener("click", () => {
      // Visual Upselling: same stage/object, no page reload
      try {
        fetch("/api/public/pricing-event", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            event: "upgrade_click",
            tier_id: "premium",
            page: "showcase",
            meta: { niche: currentNiche },
          }),
        }).catch(() => undefined);
      } catch (_) {
        /* ignore */
      }
      applyNiche(currentNiche, "premium");
    });
  }
  await applyNiche(nicheFromUrl(), tierFromUrl());
}

boot().catch((e) => {
  console.error(e);
  setBadge("Preview only");
  showPreview(String(e));
});
