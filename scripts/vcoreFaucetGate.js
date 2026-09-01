#!/usr/bin/env node
/**
 * Honest faucet gate — polls admin TON testnet balance.
 * When >= 1.2 TON → optionally deploy→transfer→verify (no fake PASS).
 * Never prints mnemonic. Never paints Genesis PASS without chain.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const ROOT = path.resolve(__dirname, "..");
const STATE = path.join(ROOT, ".runtime", "vcore_genesis_state.json");
const MIN_TON = 1.2;

async function tonapiBalance(addr) {
  const url = `https://testnet.tonapi.io/v2/accounts/${encodeURIComponent(addr)}`;
  let lastErr = null;
  for (let i = 0; i < 4; i++) {
    try {
      const res = await fetch(url, { headers: { Accept: "application/json" } });
      if (!res.ok) throw new Error(`tonapi HTTP ${res.status}`);
      const j = await res.json();
      const nano = Number(j.balance || 0);
      return {
        balanceTon: nano / 1e9,
        balanceNano: nano,
        status: j.status,
        address: j.address,
      };
    } catch (e) {
      lastErr = e;
      await new Promise((r) => setTimeout(r, 1500 * (i + 1)));
    }
  }
  // Soft-fail in watch mode — keep WAITING_FAUCET rather than crash
  return {
    balanceTon: 0,
    balanceNano: 0,
    status: "rpc_error",
    address: addr,
    error: lastErr instanceof Error ? lastErr.message : String(lastErr),
  };
}

function loadAdmin() {
  if (!fs.existsSync(STATE)) throw new Error("No genesis state — run npm run vcore:genesis:init");
  const s = JSON.parse(fs.readFileSync(STATE, "utf8"));
  if (!s.adminAddress) throw new Error("No adminAddress in state");
  return s;
}

function runNpm(script) {
  const r = spawnSync("npm", ["run", script], {
    cwd: ROOT,
    encoding: "utf8",
    shell: process.platform === "win32",
    timeout: 300_000,
  });
  return { status: r.status, out: (r.stdout || "") + (r.stderr || "") };
}

async function main() {
  const auto = process.argv.includes("--auto-deploy");
  const once = process.argv.includes("--once") || !process.argv.includes("--watch");
  const watch = process.argv.includes("--watch");
  const state = loadAdmin();
  const admin = state.adminAddress;

  console.log(
    JSON.stringify(
      {
        ok: true,
        action: "FAUCET_GATE",
        adminAddress: admin,
        explorer: `https://testnet.tonviewer.com/${admin}`,
        faucet: "https://t.me/testgiver_ton_bot",
        needTon: MIN_TON,
        stage: state.stage,
        jettonMaster: state.jettonMaster || null,
        killSwitch: state.stage !== "VERIFIED" || !state.jettonMaster ? "ARMED_BLOCK_SEND" : "CHECK_UI",
        note: "MetaMask does NOT fund TON testnet. Use Telegram faucet.",
      },
      null,
      2,
    ),
  );

  const loop = async () => {
    const bal = await tonapiBalance(admin);
    const report = {
      at: new Date().toISOString(),
      adminAddress: admin,
      balanceTon: bal.balanceTon,
      balanceNano: bal.balanceNano,
      accountStatus: bal.status,
      readyForDeploy: bal.balanceTon >= MIN_TON,
      stage: loadAdmin().stage,
      rpcError: bal.error || null,
    };
    console.log(JSON.stringify(report, null, 2));

    if (bal.balanceTon < MIN_TON) {
      console.log(
        `\nWAITING_FAUCET — send ≥ ${MIN_TON} testnet TON to:\n  ${admin}\nBot: https://t.me/testgiver_ton_bot\n`,
      );
      return false;
    }

    if (!auto) {
      console.log("Balance OK. Run with --auto-deploy to execute deploy→transfer→verify.");
      return true;
    }

    for (const step of ["vcore:genesis:deploy", "vcore:genesis:transfer", "vcore:genesis:verify"]) {
      console.log(`\n>>> ${step}`);
      const r = runNpm(step);
      console.log(r.out.slice(-1200));
      if (r.status !== 0 && r.status !== 2) {
        console.error(`FAILED ${step} exit=${r.status}`);
        process.exit(1);
      }
      // deploy may exit 2 if still waiting — check
      const st = loadAdmin();
      if (step.includes("deploy") && (st.blockers || []).includes("WAITING_FAUCET")) {
        console.error("Deploy still blocked by WAITING_FAUCET");
        process.exit(2);
      }
    }
    const final = loadAdmin();
    console.log(
      JSON.stringify(
        {
          genesisPass: final.stage === "VERIFIED" && !!final.jettonMaster,
          stage: final.stage,
          jettonMaster: final.jettonMaster,
          totalSupplyOnChain: final.totalSupplyOnChain,
          adminBalanceOnChain: final.adminBalanceOnChain,
          probeBalanceOnChain: final.probeBalanceOnChain,
        },
        null,
        2,
      ),
    );
    return true;
  };

  if (watch) {
    console.log("Watching balance every 20s… Ctrl+C to stop.");
    for (;;) {
      const ok = await loop();
      if (ok && auto) break;
      if (ok && !auto) break;
      await new Promise((r) => setTimeout(r, 20_000));
    }
  } else {
    const ok = await loop();
    process.exit(ok ? 0 : 2);
  }
}

main().catch((e) => {
  console.error(JSON.stringify({ ok: false, error: e.message || String(e) }, null, 2));
  process.exit(1);
});
