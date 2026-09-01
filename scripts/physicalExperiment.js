#!/usr/bin/env node
/**
 * Physical experiment runner — VH / Genesis / DEX discovery.
 * Does NOT invent faucet funds. Polls balance; if ≥1.2 TON → deploy→transfer→verify→DEX.
 * Never reads mnemonic into Value Hunter; uses existing genesis CLI only.
 */
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const ROOT = path.resolve(__dirname, "..");
const STATE = path.join(ROOT, ".runtime", "vcore_genesis_state.json");
const REPORT = path.join(ROOT, ".runtime", "physical_experiment_report.json");

function run(cmd, args) {
  const r = spawnSync(cmd, args, {
    cwd: ROOT,
    encoding: "utf8",
    env: { ...process.env, PYTHONUTF8: "1" },
    shell: process.platform === "win32",
    timeout: 180_000,
  });
  return {
    status: r.status,
    out: (r.stdout || "") + (r.stderr || ""),
  };
}

function loadState() {
  if (!fs.existsSync(STATE)) return null;
  return JSON.parse(fs.readFileSync(STATE, "utf8"));
}

async function tonapiBalance(addr) {
  const url = `https://testnet.tonapi.io/v2/accounts/${encodeURIComponent(addr)}`;
  const res = await fetch(url, { headers: { Accept: "application/json" } });
  if (!res.ok) return { ok: false, balanceTon: 0, error: `HTTP ${res.status}` };
  const j = await res.json();
  const nano = Number(j.balance || 0);
  return { ok: true, balanceTon: nano / 1e9, status: j.status, raw: j };
}

async function main() {
  const report = {
    at: new Date().toISOString(),
    mission: "PHYSICAL_EXPERIMENT",
    steps: [],
    blockers: [],
    what_is_needed: [],
    genesis: null,
    dex: null,
    vh1: null,
  };

  // 0 — MetaMask note (cannot automate extension)
  report.steps.push({
    id: "metamask",
    result: "CODE_FIXED",
    note: "Multi-provider + wait inject + clear RU errors. Requires Chrome/Edge with extension — not Cursor Browser. MetaMask ≠ TON signer.",
  });

  // 1 — Genesis status
  let state = loadState();
  if (!state) {
    const init = run("npm", ["run", "vcore:genesis:init"]);
    report.steps.push({ id: "genesis_init", status: init.status, tail: init.out.slice(-400) });
    state = loadState();
  }

  const admin = state?.adminAddress;
  report.genesis = { stage: state?.stage, admin, jettonMaster: state?.jettonMaster || null };

  if (!admin) {
    report.blockers.push("NO_ADMIN_ADDRESS");
    report.what_is_needed.push("Run npm run vcore:genesis:init");
  } else {
    const bal = await tonapiBalance(admin);
    report.steps.push({ id: "faucet_balance_check", ...bal, needTon: 1.2 });
    if (!bal.ok || bal.balanceTon < 1.2) {
      report.blockers.push("WAITING_FAUCET");
      report.what_is_needed.push(
        `Отправьте ≥1.2 testnet TON на ${admin} через https://t.me/testgiver_ton_bot (captcha) или https://faucet.tonxapi.com/`,
      );
      report.what_is_needed.push("Затем: npm run vcore:genesis:deploy && npm run vcore:genesis:transfer && npm run vcore:genesis:verify");
    } else {
      // deploy chain
      for (const step of [
        ["deploy", ["run", "vcore:genesis:deploy"]],
        ["transfer", ["run", "vcore:genesis:transfer"]],
        ["verify", ["run", "vcore:genesis:verify"]],
      ]) {
        const r = run("npm", step[1]);
        report.steps.push({ id: `genesis_${step[0]}`, status: r.status, tail: r.out.slice(-500) });
        if (r.status !== 0) {
          report.blockers.push(`GENESIS_${step[0].toUpperCase()}_FAILED`);
          break;
        }
      }
      state = loadState();
      report.genesis = { stage: state?.stage, admin, jettonMaster: state?.jettonMaster || null };
      if (state?.stage === "VERIFIED" && state?.jettonMaster) {
        report.steps.push({ id: "genesis_pass", result: "PASS", master: state.jettonMaster });
      } else {
        report.blockers.push("GENESIS_NOT_VERIFIED");
      }
    }
  }

  // 2 — DEX discovery (honest even without master)
  const dex = run("node", ["scripts/vcorePipelineMaster.js"]);
  report.dex = { status: dex.status, tail: dex.out.slice(-800) };
  report.steps.push({
    id: "dex_discovery",
    result: state?.jettonMaster ? "RAN" : "SKIPPED_NO_MASTER",
    note: "VCORE→DEX only after master exists; expect NO_POOL until LP capital (≠ VH-1 €0).",
  });

  // 3 — VH-1 strict hunt
  const vh = run("py", ["-3.12", "-m", "virtus_core.value_hunter", "--sources"]);
  let vhJson = null;
  try {
    const s = vh.out.indexOf("{");
    const e = vh.out.lastIndexOf("}");
    vhJson = JSON.parse(vh.out.slice(s, e + 1));
  } catch (_) {}
  report.vh1 = {
    real_external_assets: vhJson?.mission?.current ?? vhJson?.counts?.real_external_assets ?? null,
    executable_now: vhJson?.counts?.executable_now ?? null,
    candidates: vhJson?.counts?.candidates_for_test ?? null,
    message: vhJson?.message ?? null,
    counter_invariant: vhJson?.counter_invariant ?? null,
  };
  report.steps.push({
    id: "vh1",
    result: (report.vh1.real_external_assets || 0) > 0 ? "REAL_ASSET_FOUND" : "STILL_ZERO",
  });

  // Verdict
  if (report.blockers.includes("WAITING_FAUCET")) {
    report.verdict =
      "Эксперимент остановлен на физическом кране: баланс admin = 0. Код готов; нужен faucet от владельца.";
  } else if (report.blockers.length) {
    report.verdict = `Блокеры: ${report.blockers.join(", ")}`;
  } else if ((report.vh1.real_external_assets || 0) === 0) {
    report.verdict =
      "Genesis закрыт / DEX прогнан. VH-1: REAL_EXTERNAL_ASSETS всё ещё 0 — нужен внешний источник с полным REAL proof.";
  } else {
    report.verdict = "Первый REAL_EXTERNAL_ASSET зафиксирован.";
  }

  fs.mkdirSync(path.dirname(REPORT), { recursive: true });
  fs.writeFileSync(REPORT, JSON.stringify(report, null, 2), "utf8");
  console.log(JSON.stringify(report, null, 2));
  console.log("\n---\nReport:", REPORT);
  process.exit(report.blockers.includes("WAITING_FAUCET") ? 2 : report.blockers.length ? 1 : 0);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
