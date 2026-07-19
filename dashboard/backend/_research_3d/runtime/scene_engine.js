/**
 * Virtus research_3d scene engine — studio env, auto-orbit, scroll-linked spin.
 * Isolated from Path A. Loads GLB from ../scenes/<niche>/examples/*.glb
 * Uses LOCAL vendor/ Three.js (no CDN).
 */
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";

const CATALOG_URL = "../niches/examples_catalog.json";

const nicheSel = document.getElementById("niche");
const exampleSel = document.getElementById("example");
const headline = document.getElementById("headline");
const subcopy = document.getElementById("subcopy");
const statusEl = document.getElementById("status");
const fallbackEl = document.getElementById("fallback");
const viewport = document.getElementById("viewport");

let catalog = null;
let renderer;
let scene;
let camera;
let root = new THREE.Group();
let currentModel = null;
let baseSpin = 0.35;
let scrollSpin = 0;

function webglOk() {
  try {
    const c = document.createElement("canvas");
    return !!(c.getContext("webgl2") || c.getContext("webgl"));
  } catch {
    return false;
  }
}

function setStatus(msg) {
  if (statusEl) statusEl.textContent = msg;
}

function nicheIds() {
  return Object.keys(catalog.niches || {}).sort();
}

function fillNicheSelect() {
  nicheSel.innerHTML = "";
  for (const id of nicheIds()) {
    const opt = document.createElement("option");
    opt.value = id;
    opt.textContent = id;
    nicheSel.appendChild(opt);
  }
}

function fillExampleSelect(niche) {
  exampleSel.innerHTML = "";
  const rows = catalog.niches[niche] || [];
  for (const row of rows) {
    const opt = document.createElement("option");
    opt.value = row.path;
    opt.textContent = `${row.id} — ${row.title} (${row.bytes} B)`;
    opt.dataset.title = row.title;
    opt.dataset.material = row.material;
    exampleSel.appendChild(opt);
  }
}

function modelUrl(relPath) {
  return "../" + String(relPath || "").replace(/^\//, "");
}

async function loadModel(relPath, title, materialName) {
  setStatus("Loading " + relPath + "…");
  const loader = new GLTFLoader();
  const url = modelUrl(relPath);
  const gltf = await loader.loadAsync(url);
  if (currentModel) {
    root.remove(currentModel);
    currentModel.traverse((o) => {
      if (o.isMesh) {
        o.geometry?.dispose?.();
        if (Array.isArray(o.material)) o.material.forEach((m) => m.dispose?.());
        else o.material?.dispose?.();
      }
    });
  }
  currentModel = gltf.scene;
  const box = new THREE.Box3().setFromObject(currentModel);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const maxDim = Math.max(size.x, size.y, size.z) || 1;
  const scale = 1.6 / maxDim;
  currentModel.scale.setScalar(scale);
  currentModel.position.set(0, 0, 0);
  currentModel.position.sub(center.multiplyScalar(scale));
  currentModel.traverse((o) => {
    if (o.isMesh) {
      o.castShadow = true;
      o.receiveShadow = true;
    }
  });
  root.add(currentModel);
  headline.textContent = `${nicheSel.value} · ${title}`;
  subcopy.textContent = `Material: ${materialName}. Studio light · auto-orbit · scroll.`;
  setStatus("Готово — листайте страницу.");
}

function initThree() {
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(viewport.clientWidth, viewport.clientHeight);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  renderer.shadowMap.enabled = true;
  viewport.appendChild(renderer.domElement);

  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x070b12);
  camera = new THREE.PerspectiveCamera(
    40,
    viewport.clientWidth / Math.max(viewport.clientHeight, 1),
    0.1,
    100
  );
  camera.position.set(0.15, 0.55, 3.2);

  try {
    const pmrem = new THREE.PMREMGenerator(renderer);
    scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    pmrem.dispose();
  } catch (e) {
    console.warn("RoomEnvironment failed, lights only", e);
  }

  scene.add(new THREE.HemisphereLight(0xc9ddff, 0x1a1520, 0.55));
  const key = new THREE.DirectionalLight(0xffffff, 1.35);
  key.position.set(2.5, 4, 2);
  key.castShadow = true;
  scene.add(key);
  const rim = new THREE.DirectionalLight(0x88aaff, 0.55);
  rim.position.set(-3, 1.5, -2);
  scene.add(rim);

  const ground = new THREE.Mesh(
    new THREE.CircleGeometry(2.2, 48),
    new THREE.MeshStandardMaterial({ color: 0x101820, metalness: 0.2, roughness: 0.85 })
  );
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -0.85;
  ground.receiveShadow = true;
  scene.add(ground);
  scene.add(root);

  window.addEventListener("resize", () => {
    const w = viewport.clientWidth;
    const h = viewport.clientHeight;
    camera.aspect = w / Math.max(h, 1);
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  });

  window.addEventListener(
    "scroll",
    () => {
      const max = Math.max(document.body.scrollHeight - window.innerHeight, 1);
      const t = window.scrollY / max;
      scrollSpin = t * 1.8;
      camera.position.x = 0.15 + Math.sin(t * Math.PI) * 0.25;
      camera.position.y = 0.55 + t * 0.15;
      camera.lookAt(0, 0, 0);
    },
    { passive: true }
  );

  const animate = () => {
    requestAnimationFrame(animate);
    const speed = baseSpin + scrollSpin;
    root.rotation.y += 0.008 * (0.35 + speed);
    root.rotation.x = Math.sin(performance.now() * 0.0004) * 0.08;
    renderer.render(scene, camera);
  };
  animate();
}

async function boot() {
  if (!webglOk()) {
    setStatus("WebGL недоступен");
    fallbackEl.style.display = "block";
    fallbackEl.textContent =
      "Fallback: CSS-Motion Path A. Откройте fallback_demo.html";
    return;
  }

  try {
    const res = await fetch(CATALOG_URL);
    if (!res.ok) throw new Error("HTTP " + res.status + " for catalog");
    catalog = await res.json();
  } catch (e) {
    setStatus("Нет каталога: " + e);
    return;
  }

  fillNicheSelect();
  nicheSel.value = catalog.niches.dental ? "dental" : nicheIds()[0];
  fillExampleSelect(nicheSel.value);
  initThree();

  const apply = () => {
    const opt = exampleSel.selectedOptions[0];
    if (!opt) return;
    loadModel(opt.value, opt.dataset.title || opt.textContent, opt.dataset.material || "PBR").catch(
      (err) => setStatus(String(err && err.message ? err.message : err))
    );
  };

  nicheSel.addEventListener("change", () => {
    fillExampleSelect(nicheSel.value);
    apply();
  });
  exampleSel.addEventListener("change", apply);
  apply();
}

boot().catch((e) => setStatus("Boot failed: " + e));
