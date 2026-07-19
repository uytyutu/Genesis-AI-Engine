/**
 * Sold-site demo: Praxis Mueller (DE dental) — HDR + tooth GLB + CSS-Motion page.
 * On WebGL failure → Classic CSS gradient (no empty canvas).
 */
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { RGBELoader } from "three/addons/loaders/RGBELoader.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const MODEL_URL = "../../../scenes/dental/examples/01_tooth.glb";
const HDR_PATH = "../../hdr/";
const HDR_FILE = "studio_small.hdr";

const badge = document.getElementById("mode-badge");
const classic = document.getElementById("classic-fallback");
const container = document.getElementById("webgl-container");

let camera, scene, renderer, controls, model;
let scrollRotY = 0;
let mouseX = 0;
let mouseY = 0;
let windowHalfX = window.innerWidth / 2;
let windowHalfY = window.innerHeight / 2;

function webglOk() {
  try {
    const c = document.createElement("canvas");
    return !!(c.getContext("webgl2") || c.getContext("webgl"));
  } catch {
    return false;
  }
}

function activateClassic(reason) {
  document.body.classList.add("webgl-fallback");
  if (classic) classic.hidden = false;
  if (container) container.style.display = "none";
  if (badge) badge.textContent = "Classic CSS-Motion · " + reason;
}

function setBadge(msg) {
  if (badge) badge.textContent = msg;
}

async function initPremium() {
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(40, window.innerWidth / window.innerHeight, 0.1, 100);
  camera.position.set(0.15, 0.25, 3.8);

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.4;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  container.appendChild(renderer.domElement);

  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.enableZoom = false;
  controls.enablePan = false;

  scene.add(new THREE.HemisphereLight(0xddeeff, 0x1a1520, 0.4));
  const key = new THREE.DirectionalLight(0xffffff, 0.5);
  key.position.set(3, 5, 2);
  scene.add(key);

  const texture = await new RGBELoader().setPath(HDR_PATH).loadAsync(HDR_FILE);
  texture.mapping = THREE.EquirectangularReflectionMapping;
  scene.environment = texture;
  scene.background = new THREE.Color(0x071018);

  const gltf = await new GLTFLoader().loadAsync(MODEL_URL);
  model = gltf.scene;
  model.traverse((child) => {
    if (child.isMesh && child.material) {
      const mats = Array.isArray(child.material) ? child.material : [child.material];
      for (const m of mats) {
        if ("metalness" in m) m.metalness = 0.15;
        if ("roughness" in m) m.roughness = 0.12;
        m.envMapIntensity = 1.35;
        m.needsUpdate = true;
      }
    }
  });
  const box = new THREE.Box3().setFromObject(model);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const scale = 1.9 / (Math.max(size.x, size.y, size.z) || 1);
  model.scale.setScalar(scale);
  model.position.sub(center.multiplyScalar(scale));
  scene.add(model);

  setBadge("Premium 3D aktiv · scrollen / Maus bewegen");
  document.body.classList.add("loaded");
}

function onResize() {
  windowHalfX = window.innerWidth / 2;
  windowHalfY = window.innerHeight / 2;
  if (!camera || !renderer) return;
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}

function animate() {
  requestAnimationFrame(animate);
  if (model) {
    model.rotation.y = scrollRotY + mouseX * 0.001;
    model.rotation.x += (mouseY * 0.001 - model.rotation.x) * 0.08;
  }
  controls?.update();
  renderer?.render(scene, camera);
}

async function boot() {
  if (!webglOk()) {
    activateClassic("WebGL unavailable (iOS / old browser)");
    return;
  }
  try {
    await initPremium();
  } catch (e) {
    console.error(e);
    activateClassic("HDR/GLB failed");
    return;
  }

  window.addEventListener("resize", onResize);
  document.addEventListener("mousemove", (e) => {
    mouseX = (e.clientX - windowHalfX) / 2;
    mouseY = (e.clientY - windowHalfY) / 2;
  });
  window.addEventListener(
    "scroll",
    () => {
      scrollRotY = (window.scrollY / Math.max(window.innerHeight, 1)) * Math.PI * 2;
    },
    { passive: true }
  );
  animate();
}

boot();
