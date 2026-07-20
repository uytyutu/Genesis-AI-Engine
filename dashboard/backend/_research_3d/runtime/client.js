/**
 * Virtus research_3d premium player — HDR env + scroll spin + mouse parallax.
 * All Factory niches × 5 examples; markets only change UI copy.
 */
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { RGBELoader } from "three/addons/loaders/RGBELoader.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const CATALOG_URL = "../niches/examples_catalog.json";

const MARKET_COPY = {
  DE: {
    title: "Zahnarztpraxis Müller",
    sub: "Modernste Implantologie — Premium-Präsentation.",
    cta: "Termin vereinbaren",
    detailTitle: "Unsere Technologie",
    detailBody: "Hochwertige Materialien und Präzision.",
  },
  AT: {
    title: "Zahnarztpraxis Müller",
    sub: "Implantologie auf Premium-Niveau.",
    cta: "Termin vereinbaren",
    detailTitle: "Unsere Technologie",
    detailBody: "Präzision und hochwertige Materialien.",
  },
  CH: {
    title: "Zahnarztpraxis Müller",
    sub: "Implantologie mit Premium-Auftritt.",
    cta: "Termin vereinbaren",
    detailTitle: "Unsere Technologie",
    detailBody: "Hochwertige Materialien und Präzision.",
  },
  US: {
    title: "Smile Dental Studio",
    sub: "Modern implantology — premium 3D presentation.",
    cta: "Book appointment",
    detailTitle: "Our technology",
    detailBody: "High-grade materials and precision.",
  },
  GB: {
    title: "Smile Dental Studio",
    sub: "Modern implantology with a premium look.",
    cta: "Book appointment",
    detailTitle: "Our technology",
    detailBody: "High-quality materials and precision.",
  },
  UA: {
    title: "Стоматологія Мюллер",
    sub: "Сучасна імплантологія — преміум 3D.",
    cta: "Записатися",
    detailTitle: "Наша технологія",
    detailBody: "Якісні матеріали та точність.",
  },
  RU: {
    title: "Стоматология Мюллер",
    sub: "Современная имплантология — премиум 3D.",
    cta: "Записаться",
    detailTitle: "Наша технология",
    detailBody: "Качественные материалы и точность.",
  },
};

const NICHE_HEADLINES = {
  dental: { DE: "Zahnmedizin", EN: "Dental care", UK: "Стоматологія", RU: "Стоматология" },
  auto: { DE: "Autowerkstatt", EN: "Auto workshop", UK: "Автосервіс", RU: "Автосервис" },
  law: { DE: "Kanzlei", EN: "Law office", UK: "Юридична фірма", RU: "Юридическая фирма" },
  beauty: { DE: "Salon", EN: "Beauty salon", UK: "Салон краси", RU: "Салон красоты" },
  energy: { DE: "Photovoltaik", EN: "Solar energy", UK: "Сонячна енергія", RU: "Солнечная энергия" },
  green: { DE: "Garten", EN: "Garden service", UK: "Садівництво", RU: "Садоводство" },
  computer: { DE: "PC-Service", EN: "PC service", UK: "Ремонт ПК", RU: "Ремонт ПК" },
  appliance: { DE: "Hausgeräte", EN: "Appliances", UK: "Побутова техніка", RU: "Бытовая техника" },
  handwerk: { DE: "Handwerk", EN: "Craftsman", UK: "Ремісник", RU: "Мастер" },
  generic: { DE: "Lokalgeschäft", EN: "Local business", UK: "Локальний бізнес", RU: "Локальный бизнес" },
};

const els = {
  niche: document.getElementById("niche"),
  example: document.getElementById("example"),
  market: document.getElementById("market"),
  meta: document.getElementById("picker-meta"),
  status: document.getElementById("status-line"),
  heroTitle: document.getElementById("hero-title"),
  heroSub: document.getElementById("hero-sub"),
  heroCta: document.getElementById("hero-cta"),
  detailTitle: document.getElementById("detail-title"),
  detailBody: document.getElementById("detail-body"),
};

let catalog = null;
let markets = [];
let container, camera, scene, renderer, controls;
let model = null;
let scrollRotY = 0;
let mouseX = 0;
let mouseY = 0;
let windowHalfX = window.innerWidth / 2;
let windowHalfY = window.innerHeight / 2;

function setStatus(msg) {
  if (els.status) els.status.textContent = msg;
}

function modelUrl(relPath) {
  return "../" + String(relPath || "").replace(/^\//, "");
}

function langForMarket(code) {
  if (code === "DE" || code === "AT" || code === "CH") return "DE";
  if (code === "UA") return "UK";
  if (code === "RU") return "RU";
  return "EN";
}

function applyMarketCopy() {
  const market = els.market.value || "DE";
  const niche = els.niche.value || "dental";
  const base = MARKET_COPY[market] || MARKET_COPY.US;
  const lang = langForMarket(market);
  const nicheLabel =
    (NICHE_HEADLINES[niche] && NICHE_HEADLINES[niche][lang]) ||
    (NICHE_HEADLINES[niche] && NICHE_HEADLINES[niche].EN) ||
    niche;

  // Keep market-native CTA/body; title blends niche + demo brand
  if (niche === "dental") {
    els.heroTitle.textContent = base.title;
    els.heroSub.textContent = base.sub;
  } else {
    els.heroTitle.textContent = nicheLabel;
    els.heroSub.textContent = base.sub;
  }
  els.heroCta.textContent = base.cta;
  els.detailTitle.textContent = base.detailTitle;
  els.detailBody.textContent = base.detailBody;
  els.meta.textContent = `${niche} · market ${market} · HDR studio · research only`;
}

function fillMarkets() {
  els.market.innerHTML = "";
  for (const code of markets) {
    const opt = document.createElement("option");
    opt.value = code;
    opt.textContent = code;
    els.market.appendChild(opt);
  }
  els.market.value = markets.includes("DE") ? "DE" : markets[0];
}

function fillNiches() {
  els.niche.innerHTML = "";
  for (const id of Object.keys(catalog.niches || {}).sort()) {
    const opt = document.createElement("option");
    opt.value = id;
    opt.textContent = id;
    els.niche.appendChild(opt);
  }
  els.niche.value = catalog.niches.dental ? "dental" : Object.keys(catalog.niches)[0];
}

function fillExamples() {
  els.example.innerHTML = "";
  const rows = catalog.niches[els.niche.value] || [];
  for (const row of rows) {
    const opt = document.createElement("option");
    opt.value = row.path;
    opt.textContent = `${row.id} — ${row.title}`;
    opt.dataset.title = row.title;
    opt.dataset.material = row.material;
    els.example.appendChild(opt);
  }
}

function disposeModel() {
  if (!model) return;
  scene.remove(model);
  model.traverse((o) => {
    if (o.isMesh) {
      o.geometry?.dispose?.();
      if (Array.isArray(o.material)) o.material.forEach((m) => m.dispose?.());
      else o.material?.dispose?.();
    }
  });
  model = null;
}

function loadModel(relPath) {
  setStatus("Loading " + relPath + "…");
  const loader = new GLTFLoader();
  return loader.loadAsync(modelUrl(relPath)).then((gltf) => {
    disposeModel();
    model = gltf.scene;
    model.traverse((child) => {
      if (child.isMesh && child.material) {
        const mats = Array.isArray(child.material) ? child.material : [child.material];
        for (const m of mats) {
          if ("metalness" in m) m.metalness = Math.min(0.35, (m.metalness ?? 0.1) + 0.05);
          if ("roughness" in m) m.roughness = Math.min(m.roughness ?? 0.35, 0.22);
          m.envMapIntensity = 1.25;
          m.needsUpdate = true;
        }
        child.castShadow = true;
        child.receiveShadow = true;
      }
    });
    const box = new THREE.Box3().setFromObject(model);
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z) || 1;
    const scale = 1.85 / maxDim;
    model.scale.setScalar(scale);
    model.position.set(0, 0, 0);
    model.position.sub(center.multiplyScalar(scale));
    scene.add(model);
    document.body.classList.add("loaded");
    setStatus("Lab ready — PLACEHOLDER mesh (not client Premium 3D)");
  });
}

function initScene() {
  container = document.getElementById("webgl-container");
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(40, window.innerWidth / window.innerHeight, 0.1, 100);
  camera.position.set(0.2, 0.35, 4.2);

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.35;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  container.appendChild(renderer.domElement);

  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.enableZoom = false;
  controls.enablePan = false;
  controls.target.set(0, 0, 0);

  scene.add(new THREE.HemisphereLight(0xddeeff, 0x1a1520, 0.35));
  const key = new THREE.DirectionalLight(0xffffff, 0.55);
  key.position.set(3, 5, 2);
  scene.add(key);

  return new Promise((resolve, reject) => {
    new RGBELoader().setPath("hdr/").load(
      "studio_small.hdr",
      (texture) => {
        texture.mapping = THREE.EquirectangularReflectionMapping;
        scene.environment = texture;
        // Keep dark UI-friendly backdrop (not full HDR sky)
        scene.background = new THREE.Color(0x0a0e14);
        resolve();
      },
      undefined,
      reject
    );
  });
}

function onWindowResize() {
  windowHalfX = window.innerWidth / 2;
  windowHalfY = window.innerHeight / 2;
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}

function onDocumentMouseMove(event) {
  mouseX = (event.clientX - windowHalfX) / 2;
  mouseY = (event.clientY - windowHalfY) / 2;
}

function onDocumentScroll() {
  const scrollY = window.scrollY;
  const windowHeight = Math.max(window.innerHeight, 1);
  scrollRotY = (scrollY / windowHeight) * Math.PI * 2;
}

function animate() {
  requestAnimationFrame(animate);
  if (model) {
    const parallaxY = mouseX * 0.001;
    const parallaxX = mouseY * 0.001;
    model.rotation.y = scrollRotY + parallaxY;
    model.rotation.x += (parallaxX - model.rotation.x) * 0.08;
  }
  controls?.update();
  renderer.render(scene, camera);
}

function webglOk() {
  try {
    const c = document.createElement("canvas");
    return !!(c.getContext("webgl2") || c.getContext("webgl"));
  } catch {
    return false;
  }
}

function activateClassicFallback(reason) {
  document.body.classList.add("webgl-fallback");
  const overlay = document.getElementById("classic-fallback");
  if (overlay) overlay.hidden = false;
  if (container) container.style.display = "none";
  setStatus("Classic CSS fallback — " + reason);
}

async function boot() {
  if (!webglOk()) {
    activateClassicFallback("WebGL unavailable");
    return;
  }

  try {
    const [catRes, marketsMod] = await Promise.all([
      fetch(CATALOG_URL),
      fetch("../markets/index.json").then((r) => r.json()).catch(() => null),
    ]);
    if (!catRes.ok) throw new Error("catalog HTTP " + catRes.status);
    catalog = await catRes.json();
    markets = (marketsMod && marketsMod.markets) || Object.keys(MARKET_COPY);
  } catch (e) {
    setStatus("Catalog error: " + e);
    return;
  }

  fillNiches();
  fillExamples();
  fillMarkets();
  applyMarketCopy();

  try {
    await initScene();
  } catch (e) {
    activateClassicFallback("HDR/WebGL failed: " + e);
    return;
  }

  const applyModel = () => {
    const opt = els.example.selectedOptions[0];
    if (!opt) return;
    loadModel(opt.value).catch((err) => setStatus(String(err)));
  };

  els.niche.addEventListener("change", () => {
    fillExamples();
    applyMarketCopy();
    applyModel();
  });
  els.example.addEventListener("change", applyModel);
  els.market.addEventListener("change", applyMarketCopy);

  window.addEventListener("resize", onWindowResize);
  document.addEventListener("mousemove", onDocumentMouseMove);
  window.addEventListener("scroll", onDocumentScroll, { passive: true });

  applyModel();
  animate();
}

boot().catch((e) => setStatus("Boot failed: " + e));
