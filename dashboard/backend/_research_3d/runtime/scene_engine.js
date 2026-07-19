/**
 * Virtus research_3d scene engine — studio env, auto-orbit, scroll-linked spin.
 * Isolated from Path A. Loads GLB from ../scenes/<niche>/examples/*.glb
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
let frame = 0;

function webglOk() {
  try {
    const c = document.createElement("canvas");
    return !!(c.getContext("webgl2") || c.getContext("webgl"));
  } catch {
    return false;
  }
}

function setStatus(msg) {
  statusEl.textContent = msg;
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
  // scenes/... from runtime/
  return "../" + relPath.replace(/^scenes\//, "scenes/");
}

async function loadModel(relPath, title, materialName) {
  setStatus("Loading " + relPath + "…");
  const loader = new GLTFLoader();
  const gltf = await loader.loadAsync(modelUrl(relPath));
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
  // Fit
  const box = new THREE.Box3().setFromObject(currentModel);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const maxDim = Math.max(size.x, size.y, size.z) || 1;
  const scale = 1.6 / maxDim;
  currentModel.position.sub(center.multiplyScalar(scale));
  currentModel.scale.setScalar(scale);
  currentModel.traverse((o) => {
    if (o.isMesh) {
      o.castShadow = true;
      o.receiveShadow = true;
    }
  });
  root.add(currentModel);
  headline.textContent = `${nicheSel.value} · ${title}`;
  subcopy.textContent = `Material: ${materialName}. Studio RoomEnvironment · auto-orbit · scroll boost.`;
  setStatus("Ready — scroll the page to feel motion.");
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

  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  pmrem.dispose();

  const hemi = new THREE.HemisphereLight(0xc9ddff, 0x1a1520, 0.55);
  scene.add(hemi);
  const key = new THREE.DirectionalLight(0xffffff, 1.35);
  key.position.set(2.5, 4, 2);
  key.castShadow = true;
  scene.add(key);
  const rim = new THREE.DirectionalLight(0x88aaff, 0.55);
  rim.position.set(-3, 1.5, -2);
  scene.add(rim);

  const ground = new THREE.Mesh(
    new THREE.CircleGeometry(2.2, 48),
    new THREE.MeshStandardMaterial({
      color: 0x101820,
      metalness: 0.2,
      roughness: 0.85,
    })
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
      // gentle parallax on camera
      camera.position.x = 0.15 + Math.sin(t * Math.PI) * 0.25;
      camera.position.y = 0.55 + t * 0.15;
      camera.lookAt(0, 0, 0);
    },
    { passive: true }
  );

  const animate = () => {
    frame = requestAnimationFrame(animate);
    const speed = baseSpin + scrollSpin;
    root.rotation.y += 0.008 * (0.35 + speed);
    root.rotation.x = Math.sin(performance.now() * 0.0004) * 0.08;
    renderer.render(scene, camera);
  };
  animate();
}

async function boot() {
  if (!webglOk()) {
    setStatus("WebGL unavailable");
    fallbackEl.style.display = "block";
    fallbackEl.textContent =
      "Fallback: use CSS-Motion Path A. Open fallback_demo.html — 3D will not run on this device.";
    return;
  }

  try {
    catalog = await (await fetch(CATALOG_URL)).json();
  } catch (e) {
    setStatus("Catalog missing — run generate_research_3d_presets.py");
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
      (err) => setStatus(String(err))
    );
  };

  nicheSel.addEventListener("change", () => {
    fillExampleSelect(nicheSel.value);
    apply();
  });
  exampleSel.addEventListener("change", apply);
  apply();
}

boot();
