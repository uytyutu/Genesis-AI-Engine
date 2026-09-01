/**
 * Virtus Core · локальный ИИ-агент BTC sweep (Human-in-the-Loop).
 *
 * 1. Скан UTXO (mempool.space)
 * 2. Расчёт комиссии + фильтр пыли
 * 3. Детальный отчёт в терминале
 * 4. Запрос y/N перед подписью и broadcast
 *
 * Ключи только из .env.btc на этом ПК — не на сервер Virtus.
 *
 *   npm run agent:sweep
 *   node scripts/aiAgentSweeper.js --dry-run   # только отчёт
 *   node scripts/aiAgentSweeper.js --force     # включить неподтверждённые UTXO
 */
"use strict";

const readline = require("readline");
const {
  loadEnvFiles,
  getConfig,
  auditSweepPlan,
  buildSignedTransaction,
  broadcastSignedTx,
  printAuditReport,
} = require("./lib/btcSweepCore");

const DRY_RUN = process.argv.includes("--dry-run");
const FORCE = process.argv.includes("--force");
const AUTO_YES = process.argv.includes("--yes");

function die(msg, code = 1) {
  console.error("\n[АГЕНТ · ОТКАЗ]", msg);
  console.error("Транзакция не подписана и не отправлена.\n");
  process.exit(code);
}

function ask(question) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  return new Promise((resolve) => {
    rl.question(question, (answer) => {
      rl.close();
      resolve(answer.trim().toLowerCase());
    });
  });
}

async function main() {
  loadEnvFiles();
  const cfg = getConfig({ force: FORCE });

  console.log("══════════════════════════════════════════════════════════");
  console.log(" Virtus Agent · аудит и сбор BTC-остатков");
  console.log(" Human-in-the-Loop · ключи только локально");
  console.log("══════════════════════════════════════════════════════════");

  let plan;
  try {
    console.log("\n[1/4] Скан сети и расчёт комиссий…");
    plan = await auditSweepPlan(cfg);
    printAuditReport(plan);
  } catch (e) {
    die(e instanceof Error ? e.message : String(e));
  }

  if (!plan.profitable) {
    die(
      plan.spendable.length === 0
        ? "Нечего выводить — только пыль или нет UTXO."
        : `Пакет убыточен: net=${plan.net} sats. Дождитесь более низкой комиссии.`,
      0,
    );
  }

  if (DRY_RUN) {
    console.log("[DRY-RUN] Отчёт готов. Broadcast не выполняется.\n");
    process.exit(0);
  }

  console.log("[2/4] Ожидание подтверждения человека…");
  console.log("");
  console.log("  ⚠  Будет подписана и отправлена транзакция в Bitcoin mainnet.");
  console.log(`  ⚠  Получатель: ${plan.vault}`);
  console.log(`  ⚠  Net после газа: ${plan.net} sats`);
  console.log("");

  let answer = "n";
  if (AUTO_YES) {
    console.log("  (--yes) Автоподтверждение включено.");
    answer = "y";
  } else {
    answer = await ask("  Подписать и отправить? [y/N]: ");
  }

  if (answer !== "y" && answer !== "yes" && answer !== "д" && answer !== "да") {
    console.log("\n[ОТМЕНА] Пользователь отказался. Tx не создана.\n");
    process.exit(0);
  }

  let signed;
  try {
    console.log("\n[3/4] Локальная подпись в памяти…");
    signed = buildSignedTransaction(plan);
    console.log(`  txid: ${signed.txid}`);
    console.log(`  hex:  ${signed.hex.length} байт`);
  } catch (e) {
    die(e instanceof Error ? e.message : String(e));
  }

  try {
    console.log("\n[4/4] Broadcast → mempool.space…");
    const txid = await broadcastSignedTx(cfg, signed.hex);
    console.log("\n[УСПЕХ] Транзакция принята сетью.");
    console.log(`  txid: ${txid}`);
    console.log(`  https://mempool.space/tx/${txid}\n`);
  } catch (e) {
    die(`Broadcast отклонён: ${e instanceof Error ? e.message : e}`);
  }
}

main().catch((e) => die(e instanceof Error ? e.message : String(e)));
