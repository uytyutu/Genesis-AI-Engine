#!/usr/bin/env node
/**
 * VCORE Genesis CLI — TON testnet identity gate only.
 *
 *   npm run vcore:genesis:init
 *   npm run vcore:genesis:deploy
 *   npm run vcore:genesis:transfer
 *   npm run vcore:genesis:verify
 *   npm run vcore:genesis
 *
 * NO LP · NO mainnet · NO COMMIT of .env.ton
 */
"use strict";

const {
  genesisInit,
  genesisDeploy,
  genesisTransfer,
  genesisVerify,
  genesisStatus,
} = require("./lib/vcoreGenesisCore");

async function main() {
  const cmd = (process.argv[2] || "status").toLowerCase();
  let out;
  switch (cmd) {
    case "init":
      out = await genesisInit({ forceNewMnemonic: process.argv.includes("--new") });
      break;
    case "deploy":
      out = await genesisDeploy();
      break;
    case "transfer":
      out = await genesisTransfer({
        amountHuman: process.argv[3] || "1000",
      });
      break;
    case "verify":
      out = await genesisVerify();
      break;
    case "status":
    default:
      out = await genesisStatus();
      break;
  }

  const summary = {
    stage: out.stage,
    status: out.status,
    network: out.network,
    adminAddress: out.adminAddress,
    jettonMaster: out.jettonMaster,
    totalSupplyOnChain: out.totalSupplyOnChain,
    adminBalanceOnChain: out.adminBalanceOnChain,
    probeBalanceOnChain: out.probeBalanceOnChain,
    tonBalance: out.tonBalance,
    blockers: out.blockers,
    valueLayers: out.valueLayers,
    explorer: out.explorer,
    next: out.next,
    gates: out.gates,
    logHead: (out.log || []).slice(0, 5),
  };
  console.log(JSON.stringify(summary, null, 2));

  if (out.error === "WAITING_FAUCET" || (out.blockers || []).includes("WAITING_FAUCET")) {
    process.exitCode = 2;
  }
}

main().catch((e) => {
  console.error(JSON.stringify({ ok: false, error: e.message || String(e) }, null, 2));
  process.exit(1);
});
