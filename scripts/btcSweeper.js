/**
 * Virtus Core — локальный BTC sweeper (ТОЛЬКО СВОИ КЛЮЧИ).
 * Обёртка над btcSweepCore. Для интерактива используйте: npm run agent:sweep
 */
"use strict";

const {
  loadEnvFiles,
  getConfig,
  auditSweepPlan,
  buildSignedTransaction,
  broadcastSignedTx,
  printAuditReport,
} = require("./lib/btcSweepCore");

const WANT_BROADCAST = process.argv.includes("--broadcast");
const FORCE = process.argv.includes("--force");

function die(msg) {
  console.error("\n[ОШИБКА]", msg);
  process.exit(1);
}

async function main() {
  loadEnvFiles();
  const cfg = getConfig({ force: FORCE });

  console.log("══════════════════════════════════════════════");
  console.log(" Virtus Core · локальный BTC sweeper");
  console.log(" Только свои UTXO · ключи только на этом ПК");
  console.log("══════════════════════════════════════════════");
  console.log(
    WANT_BROADCAST ? " Режим: BROADCAST" : " Режим: DRY-RUN · HITL: npm run agent:sweep",
  );

  let plan;
  try {
    plan = await auditSweepPlan(cfg);
    printAuditReport(plan);
  } catch (e) {
    die(e instanceof Error ? e.message : String(e));
  }

  if (!plan.profitable) {
    console.log("\nНечего сводить или пакет убыточен.");
    process.exit(0);
  }

  let signed;
  try {
    signed = buildSignedTransaction(plan);
  } catch (e) {
    die(e instanceof Error ? e.message : String(e));
  }

  console.log("\n── Подписано локально ──");
  console.log(" txid:", signed.txid);

  if (!WANT_BROADCAST) {
    console.log("\nDRY-RUN. Broadcast: npm run btc:sweep:broadcast");
    console.log("Или с подтверждением: npm run agent:sweep");
    process.exit(0);
  }

  try {
    const txid = await broadcastSignedTx(cfg, signed.hex);
    console.log("\nOK:", txid);
    console.log(`https://mempool.space/tx/${txid}`);
  } catch (e) {
    die(e instanceof Error ? e.message : String(e));
  }
}

main().catch((e) => die(e instanceof Error ? e.message : String(e)));
