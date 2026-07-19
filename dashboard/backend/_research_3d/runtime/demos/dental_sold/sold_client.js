/**
 * Sold-site demo shell — showcase assets come from Showcase Library by niche.
 * Default niche=dental for Praxis Mueller demo; any ?niche= works.
 */
const HERO_URL = "assets/hero_clinic.jpg";
const HDR_PATH = "../../hdr/";
const HDR_FILE = "studio_small.hdr";
const LOAD_TIMEOUT_MS = 12000;

function nicheFromPage() {
  const q = new URLSearchParams(location.search).get("niche");
  if (q) return q.trim().toLowerCase();
  return (document.body.dataset.niche || "dental").toLowerCase();
}

function showcaseBase(niche) {
  return `../../../showcases/${niche}/`;
}

let currentNiche = nicheFromPage();
let qualityMeta = {
  quality: "placeholder",
  client_facing_3d: false,
  label_de: "Premium Showcase",
  sub_de: "Digitale Präsentation moderner Technologien.",
};
let REGISTRY_QUALITY = showcaseBase(currentNiche) + "quality.json";
let REGISTRY_PREVIEW = showcaseBase(currentNiche) + "preview.jpg?v=lib1";
let REGISTRY_MODEL = showcaseBase(currentNiche) + "model.glb?v=lib1";

function refreshRegistryPaths(niche) {
  currentNiche = niche;
  const base = showcaseBase(niche);
  REGISTRY_QUALITY = base + "quality.json";
  REGISTRY_PREVIEW = base + (qualityMeta.preview || "preview.jpg") + "?v=lib1";
  REGISTRY_MODEL = base + (qualityMeta.model || "model.glb") + "?v=lib1";
}

const els = {
  badge: document.getElementById("mode-badge"),
  tierPill: document.getElementById("tier-pill"),
  photo: document.getElementById("photo-hero"),
  stage: document.getElementById("showcase-stage"),
  loading: document.getElementById("showcase-loading"),
  loadingText: document.getElementById("showcase-loading-text"),
  still: document.getElementById("showcase-still"),
  canvasWrap: document.getElementById("showcase-canvas-wrap"),
  hint: document.getElementById("showcase-hint"),
  title: document.getElementById("showcase-title"),
  sub: document.getElementById("showcase-sub"),
  kicker: document.getElementById("showcase-kicker"),
  root: document.querySelector("[data-showcase-root]"),
  upgradeBtn: document.getElementById("upgrade-premium"),
};

let currentTier = "premium";
let threeSession = null;

function setBadge(msg) {
  if (els.badge) els.badge.textContent = msg;
}

function setUpsellVisible(show) {
  if (!els.upgradeBtn) return;
  els.upgradeBtn.hidden = !show;
}

function withTimeout(promise, ms, label) {
  return Promise.race([
    promise,
    new Promise((_, reject) =>
      setTimeout(() => reject(new Error(label + " timeout " + ms + "ms")), ms)
    ),
  ]);
}

function tierFromUrl() {
  const t = new URLSearchParams(location.search).get("tier");
  if (t === "basic" || t === "business" || t === "premium") return t;
  return "premium";
}

function applyTierChrome(tier) {
  currentTier = tier;
  document.body.dataset.tier = tier;
  document.body.classList.remove("tier-basic", "tier-business", "tier-premium");
  document.body.classList.add("tier-" + tier);
  document.querySelectorAll("#tier-switch button").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tier === tier);
  });
  const pills = {
    basic: "Basic: Fotos",
    business: "Business: Foto + CSS + Preview",
    premium: "Premium: Showcase",
  };
  if (els.tierPill) els.tierPill.textContent = pills[tier] || pills.premium;
  const url = new URL(location.href);
  url.searchParams.set("tier", tier);
  history.replaceState({}, "", url);
}

function showHero() {
  if (!els.photo) return;
  els.photo.hidden = false;
  els.photo.style.backgroundImage = `url("${HERO_URL}")`;
}

function showPreview(reason) {
  if (els.still) {
    els.still.hidden = false;
    els.still.style.backgroundImage = `url("${REGISTRY_PREVIEW}")`;
    els.still.classList.add("is-visible");
    els.still.classList.remove("is-dimmed");
  }
  if (els.loading) els.loading.hidden = true;
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
  // Lab override for developing GLB — never default Premium path
  if (new URLSearchParams(location.search).get("lab3d") === "1") return true;
  const q = String(qualityMeta.quality || "").toLowerCase();
  return (
    qualityMeta.client_facing_3d === true &&
    (q === "approved" || q === "premium")
  );
}

async function loadQuality() {
  refreshRegistryPaths(currentNiche);
  try {
    const res = await fetch(REGISTRY_QUALITY);
    if (!res.ok) throw new Error("quality.json HTTP " + res.status);
    qualityMeta = await res.json();
  } catch (e) {
    console.warn("[showcase] quality.json", e);
  }
  refreshRegistryPaths(currentNiche);
  if (els.title) {
    els.title.textContent =
      qualityMeta.label_de || currentNiche;
  }
  if (els.sub && qualityMeta.sub_de) {
    els.sub.textContent = qualityMeta.sub_de;
  }
  if (els.kicker) {
    els.kicker.textContent =
      "Showcase Library · " +
      currentNiche +
      " · quality=" +
      (qualityMeta.quality || "?");
  }
}

/**
 * Normalize model size + fit camera (lab-proven: scale to unit size, then aim).
 * Tiny research stubs (~0.5u) otherwise look like a clipped tip under autoRotate.
 * Idempotent: always resets scale/position before measuring.
 */
function frameObject(THREE, camera, controls, object, dim) {
  object.scale.setScalar(1);
  object.position.set(0, 0, 0);
  object.updateMatrixWorld(true);

  const box = new THREE.Box3().setFromObject(object);
  if (box.isEmpty()) {
    console.warn("[showcase] empty bbox — skip frame");
    return;
  }
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const maxDim = Math.max(size.x, size.y, size.z, 0.001);

  // Bring every niche stub to a similar on-screen size
  const targetSize = 1.75;
  const scale = targetSize / maxDim;
  object.scale.setScalar(scale);
  object.position.set(0, 0, 0);
  object.position.sub(center.clone().multiplyScalar(scale));
  object.updateMatrixWorld(true);

  camera.aspect = dim.w / Math.max(dim.h, 1);
  const fov = (camera.fov * Math.PI) / 180;
  const halfFov = Math.tan(fov / 2);
  const scaledH = size.y * scale;
  const scaledW = size.x * scale;
  const distForHeight = scaledH / 2 / halfFov;
  const distForWidth = scaledW / 2 / (halfFov * Math.max(camera.aspect, 0.1));
  const dist = Math.max(distForHeight, distForWidth, targetSize * 0.9) * 2.35;

  camera.near = Math.max(dist / 100, 0.01);
  camera.far = Math.max(dist * 100, 100);
  camera.position.set(dist * 0.28, dist * 0.22, dist);
  camera.up.set(0, 1, 0);
  camera.lookAt(0, 0, 0);
  camera.updateProjectionMatrix();

  if (controls) {
    controls.target.set(0, 0, 0);
    controls.minDistance = dist * 0.45;
    controls.maxDistance = dist * 5;
    controls.update();
  }

  console.info("[showcase] framed", {
    size: { x: size.x, y: size.y, z: size.z },
    scale,
    dist,
    cam: camera.position.toArray(),
  });
}

async function mountInteractive() {
  showLoading();
  // Keep preview visible underneath until 3D ready
  if (els.still) {
    els.still.classList.add("is-visible");
    els.still.classList.add("is-dimmed");
  }

  const THREE = await withTimeout(import("three"), LOAD_TIMEOUT_MS, "three import");
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
  // Non-zero start so OrbitControls never initializes at origin→origin (radius≈0)
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

  // HDR optional — must not block forever
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

  const modelUrl = new URL(REGISTRY_MODEL, window.location.href).href;
  console.info("[showcase] GET model", modelUrl);

  const probe = await fetch(modelUrl);
  console.info("[showcase] model HTTP", probe.status, probe.headers.get("content-length"));
  if (!probe.ok) {
    throw new Error("model.glb HTTP " + probe.status);
  }

  const gltf = await withTimeout(
    new GLTFLoader().loadAsync(modelUrl),
    LOAD_TIMEOUT_MS,
    "GLTFLoader.load"
  );
  const model = gltf.scene;
  // Keep authored PBR (titanium / ceramic). Only ensure env reflections read well.
  model.traverse((obj) => {
    if (obj.isMesh && obj.material) {
      const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
      for (const m of mats) {
        if ("envMapIntensity" in m) m.envMapIntensity = 1.55;
        m.needsUpdate = true;
      }
      obj.castShadow = false;
    }
  });
  scene.add(model);

  // Frame once before controls, once after (OrbitControls must not init at origin→origin)
  frameObject(THREE, camera, null, model, { w, h });
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.enablePan = false;
  controls.autoRotate = true;
  controls.autoRotateSpeed = 0.55;
  frameObject(THREE, camera, controls, model, { w, h });

  let alive = true;

  // Premium feel: slow auto-spin; user takes over on hover/drag; idle resumes spin
  const IDLE_RESUME_MS = 2800;
  let idleTimer = 0;
  function pauseAutoRotate() {
    controls.autoRotate = false;
    window.clearTimeout(idleTimer);
  }
  function scheduleAutoRotate() {
    window.clearTimeout(idleTimer);
    idleTimer = window.setTimeout(() => {
      if (alive) controls.autoRotate = true;
    }, IDLE_RESUME_MS);
  }
  const canvasEl = renderer.domElement;
  canvasEl.addEventListener("pointerdown", pauseAutoRotate);
  canvasEl.addEventListener("pointerup", scheduleAutoRotate);
  canvasEl.addEventListener("pointerleave", scheduleAutoRotate);
  canvasEl.addEventListener("wheel", () => {
    pauseAutoRotate();
    scheduleAutoRotate();
  }, { passive: true });

  // Prove first frame
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
      if (window.__showcaseDebug) delete window.__showcaseDebug;
    },
  };

  if (new URLSearchParams(location.search).has("debug")) {
    window.__showcaseDebug = { camera, controls, model, scene, renderer, size: { w, h } };
  }

  console.info("[showcase] interactive ready", {
    w,
    h,
    children: scene.children.length,
  });
}

async function runShowcase(tier) {
  disposeThree();
  showPreview("");
  setUpsellVisible(false);
  if (els.still) els.still.classList.remove("is-premium-still");

  if (tier === "basic") {
    if (els.root) els.root.style.display = "none";
    setBadge("Basic · Fotos (kein Showcase)");
    return;
  }
  if (els.root) els.root.style.display = "";

  // Always paint preview first (never empty)
  showPreview("");

  if (tier === "business") {
    if (els.still) els.still.classList.add("is-premium-still");
    setUpsellVisible(true);
    showPreview(
      "Business: Preview · Upgrade to Premium — dasselbe Objekt wird lebendig."
    );
    setBadge("Business · Preview");
    return;
  }

  // Premium — photoreal still until licensed studio GLB (quality=approved)
  if (!allowsInteractive3d()) {
    if (els.still) els.still.classList.add("is-premium-still");
    showPreview(
      "Premium-Präsentation · fotorealistisches Still · interaktives 3D nach Freigabe studio-Asset"
    );
    setBadge("Premium · digitale Präsentation");
    return;
  }

  const start = async () => {
    try {
      await mountInteractive();
      setBadge(
        new URLSearchParams(location.search).get("lab3d") === "1"
          ? "Lab · interaktives 3D"
          : "Premium · interaktives 3D"
      );
      if (els.hint) {
        els.hint.textContent =
          "3D geladen · drehen / zoomen · transparenter Glass-Stage";
      }
    } catch (e) {
      console.error("[showcase] 3D failed → preview fallback", e);
      disposeThree();
      showPreview(
        "3D-Fallback: " + (e && e.message ? e.message : String(e)) + " · Preview bleibt."
      );
      setBadge("Premium · Preview (3D-Fehler)");
    }
  };

  if (!("IntersectionObserver" in window) || !els.root) {
    await start();
    return;
  }

  // If already in view, start immediately; else wait
  const rect = els.root.getBoundingClientRect();
  const inView = rect.top < window.innerHeight + 160 && rect.bottom > -40;
  if (inView) {
    await start();
    return;
  }

  await new Promise((resolve) => {
    const io = new IntersectionObserver(
      (entries) => {
        if (!entries.some((e) => e.isIntersecting)) return;
        io.disconnect();
        start().finally(resolve);
      },
      { rootMargin: "200px", threshold: 0.01 }
    );
    io.observe(els.root);
  });
}

async function applyTier(tier) {
  applyTierChrome(tier);
  showHero();
  await runShowcase(tier);
}

async function boot() {
  // Preview immediately (before any async 3D)
  if (els.still) {
    els.still.style.backgroundImage = `url("${REGISTRY_PREVIEW}")`;
    els.still.classList.add("is-visible");
  }
  showHero();
  await loadQuality();
  document.querySelectorAll("#tier-switch button").forEach((btn) => {
    btn.addEventListener("click", () => applyTier(btn.dataset.tier));
  });
  if (els.upgradeBtn) {
    els.upgradeBtn.addEventListener("click", () => {
      // Visual Upselling: same stage/object, no reload
      try {
        fetch("/api/public/pricing-event", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            event: "upgrade_click",
            tier_id: "premium",
            page: "dental_sold",
            meta: { niche: "dental" },
          }),
        }).catch(() => undefined);
      } catch (_) {
        /* ignore */
      }
      applyTier("premium");
    });
  }
  await applyTier(tierFromUrl());
}

boot().catch((e) => {
  console.error(e);
  showPreview("Boot-Fallback: " + String(e));
  setBadge("Preview only");
});
