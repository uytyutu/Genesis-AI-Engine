/**
 * Общая логика BTC sweep для btcSweeper.js и aiAgentSweeper.js.
 * Только свои ключи · mempool.space · фильтр пыли.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const bitcoin = require("bitcoinjs-lib");
const bip39 = require("bip39");
const { BIP32Factory } = require("bip32");
const { ECPairFactory } = require("ecpair");
const ecc = require("tiny-secp256k1");

const ECPair = ECPairFactory(ecc);
const bip32 = BIP32Factory(ecc);
const network = bitcoin.networks.bitcoin;

const ROOT = path.resolve(__dirname, "..", "..");

function loadEnvFiles() {
  for (const name of [".env.btc", ".env", "dashboard/frontend/.env.local"]) {
    const p = path.join(ROOT, name);
    if (fs.existsSync(p)) {
      require("dotenv").config({ path: p, override: false });
    }
  }
}

function parseList(raw) {
  if (!raw) return [];
  return raw
    .split(/[\n,;\s]+/)
    .map((s) => s.trim())
    .filter(Boolean);
}

function getConfig(opts = {}) {
  return {
    mempool: (process.env.MEMPOOL_API || "https://mempool.space/api").replace(/\/$/, ""),
    vault: (process.env.VAULT_BTC_ADDRESS || "").trim(),
    feeMode: process.env.BTC_FEE_MODE || "hour",
    deriveCount: Math.min(20, Math.max(1, Number(process.env.BTC_DERIVE_COUNT || 5))),
    force: !!opts.force,
  };
}

async function mempoolGet(mempoolBase, p) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 25_000);
  try {
    const res = await fetch(`${mempoolBase}${p}`, { signal: ctrl.signal });
    if (!res.ok) throw new Error(`mempool HTTP ${res.status} для ${p}`);
    return await res.json();
  } catch (e) {
    if (e instanceof Error && e.name === "AbortError") {
      throw new Error(`Таймаут mempool.space (${p})`);
    }
    throw e;
  } finally {
    clearTimeout(t);
  }
}

async function mempoolPost(mempoolBase, p, body) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 30_000);
  try {
    const res = await fetch(`${mempoolBase}${p}`, {
      method: "POST",
      headers: { "Content-Type": "text/plain" },
      body,
      signal: ctrl.signal,
    });
    const text = await res.text();
    if (!res.ok) throw new Error(`mempool POST ${res.status}: ${text}`);
    return text.trim();
  } catch (e) {
    if (e instanceof Error && e.name === "AbortError") {
      throw new Error("Таймаут broadcast mempool.space");
    }
    throw e;
  } finally {
    clearTimeout(t);
  }
}

/** @returns {{ address: string, keyPair: import('ecpair').ECPairInterface }[]} */
function loadSigners(cfg) {
  const seed = (process.env.BTC_WALLET_SEED || "").trim();
  const wif = (process.env.BTC_PRIVATE_KEY || "").trim();
  const explicit = parseList(process.env.BTC_ADDRESSES);
  const out = [];
  const errors = [];

  if (wif) {
    try {
      const keyPair = ECPair.fromWIF(wif, network);
      const { address } = bitcoin.payments.p2wpkh({ pubkey: keyPair.publicKey, network });
      if (!address) throw new Error("не удалось вывести адрес из WIF");
      if (explicit.length && !explicit.includes(address)) {
        errors.push(`BTC_ADDRESSES не содержит адрес WIF — используем ${address}`);
      }
      out.push({ address, keyPair });
    } catch {
      throw new Error("BTC_PRIVATE_KEY: невалидный WIF");
    }
  }

  if (seed) {
    if (!bip39.validateMnemonic(seed)) {
      throw new Error("BTC_WALLET_SEED: невалидная BIP39-фраза");
    }
    const root = bip32.fromSeed(bip39.mnemonicToSeedSync(seed), network);
    for (let i = 0; i < cfg.deriveCount; i++) {
      const node = root.derivePath(`m/84'/0'/0'/0/${i}`);
      const keyPair = ECPair.fromPrivateKey(node.privateKey, { network });
      const { address } = bitcoin.payments.p2wpkh({ pubkey: keyPair.publicKey, network });
      if (address) out.push({ address, keyPair });
    }
  }

  if (out.length === 0) {
    throw new Error(
      "Нет ключей: задайте BTC_PRIVATE_KEY и/или BTC_WALLET_SEED в .env.btc (только свои).",
    );
  }

  const seen = new Set();
  const unique = out.filter((s) => {
    if (seen.has(s.address)) return false;
    seen.add(s.address);
    return true;
  });

  return { signers: unique, warnings: errors };
}

function validateVault(vault) {
  if (!vault) throw new Error("Укажите VAULT_BTC_ADDRESS в .env.btc");
  try {
    bitcoin.address.toOutputScript(vault, network);
  } catch {
    throw new Error("VAULT_BTC_ADDRESS невалиден для Bitcoin mainnet");
  }
}

function estimateVbytes(inputCount, outputCount) {
  return Math.ceil(inputCount * 68 + outputCount * 31 + 10.5);
}

function pickFeeRate(fees, mode) {
  switch (mode) {
    case "fastest":
      return fees.fastestFee;
    case "halfHour":
      return fees.halfHourFee;
    case "economy":
      return fees.economyFee;
    default:
      return fees.hourFee;
  }
}

function satsToBtc(sats) {
  return (sats / 1e8).toFixed(8);
}

/**
 * Полный аудит: UTXO, пыль, план комиссий.
 */
async function auditSweepPlan(cfg) {
  validateVault(cfg.vault);
  const { signers, warnings } = loadSigners(cfg);

  let fees;
  try {
    fees = await mempoolGet(cfg.mempool, "/v1/fees/recommended");
  } catch (e) {
    throw new Error(`API комиссий недоступен: ${e instanceof Error ? e.message : e}`);
  }

  const satPerVbyte = pickFeeRate(fees, cfg.feeMode);

  /** @type {{ txid: string, vout: number, value: number, address: string, keyPair: any, singleFee: number, dust: boolean, confirmed: boolean }[]} */
  const allUtxos = [];
  const spendable = [];
  let dustSkipped = 0;
  let unconfirmedSkipped = 0;

  for (const { address, keyPair } of signers) {
    let utxos;
    try {
      utxos = await mempoolGet(cfg.mempool, `/address/${address}/utxo`);
    } catch (e) {
      throw new Error(`Скан ${address}: ${e instanceof Error ? e.message : e}`);
    }
    if (!Array.isArray(utxos)) continue;

    for (const u of utxos) {
      const value = Number(u.value);
      const singleFee = estimateVbytes(1, 1) * satPerVbyte;
      const confirmed = !!u.status?.confirmed;
      const isDust = value <= singleFee;
      const row = {
        txid: u.txid,
        vout: u.vout,
        value,
        address,
        keyPair,
        singleFee,
        dust: isDust,
        confirmed,
      };
      allUtxos.push(row);

      if (isDust) {
        dustSkipped += 1;
        continue;
      }
      if (!confirmed && !cfg.force) {
        unconfirmedSkipped += 1;
        continue;
      }
      spendable.push(row);
    }
  }

  const totalIn = spendable.reduce((s, u) => s + u.value, 0);
  const vbytes = spendable.length > 0 ? estimateVbytes(spendable.length, 1) : 0;
  const feeSats = vbytes * satPerVbyte;
  const net = totalIn - feeSats;

  return {
    signers,
    warnings,
    fees,
    satPerVbyte,
    feeMode: cfg.feeMode,
    vault: cfg.vault,
    allUtxos,
    spendable,
    dustSkipped,
    unconfirmedSkipped,
    totalIn,
    vbytes,
    feeSats,
    net,
    profitable: spendable.length > 0 && net > 0 && feeSats < totalIn,
  };
}

function assertProfitablePlan(plan) {
  if (plan.spendable.length === 0) {
    throw new Error("Нет UTXO для вывода (всё пыль или неподтверждено).");
  }
  if (plan.net <= 0) {
    throw new Error(
      `Убыточно: net=${plan.net} sats после комиссии ${plan.feeSats}. Транзакция не будет собрана.`,
    );
  }
  if (plan.feeSats >= plan.totalIn) {
    throw new Error("Комиссия ≥ суммы входов — отмена (защита от убыточной tx).");
  }
}

function buildSignedTransaction(plan) {
  assertProfitablePlan(plan);
  const psbt = new bitcoin.Psbt({ network });
  for (const u of plan.spendable) {
    const payment = bitcoin.payments.p2wpkh({ pubkey: u.keyPair.publicKey, network });
    psbt.addInput({
      hash: u.txid,
      index: u.vout,
      witnessUtxo: { script: payment.output, value: u.value },
    });
  }
  psbt.addOutput({ address: plan.vault, value: plan.net });
  for (let i = 0; i < plan.spendable.length; i++) {
    try {
      psbt.signInput(i, plan.spendable[i].keyPair);
    } catch {
      throw new Error(`Подпись входа #${i} не удалась — проверьте ключ для ${plan.spendable[i].address}`);
    }
  }
  try {
    psbt.finalizeAllInputs();
  } catch {
    throw new Error("Finalize PSBT не удался — повреждённая или неполная транзакция.");
  }
  const tx = psbt.extractTransaction();
  return { hex: tx.toHex(), txid: tx.getId() };
}

async function broadcastSignedTx(cfg, hex) {
  return mempoolPost(cfg.mempool, "/tx", hex);
}

function printAuditReport(plan) {
  console.log("\n╔══════════════════════════════════════════════════════════╗");
  console.log("║  ОТЧЁТ АГЕНТА · BTC остатки (Human-in-the-Loop)         ║");
  console.log("╚══════════════════════════════════════════════════════════╝\n");

  if (plan.warnings.length) {
    for (const w of plan.warnings) console.log("  [!]", w);
    console.log("");
  }

  console.log(`  Vault:           ${plan.vault}`);
  console.log(`  Адресов:         ${plan.signers.length}`);
  console.log(`  Комиссия:        ${plan.satPerVbyte} sat/vB (${plan.feeMode})`);
  console.log(`  fastest/hour/eco: ${plan.fees.fastestFee}/${plan.fees.hourFee}/${plan.fees.economyFee}`);
  console.log("");

  console.log("  ── UTXO ──");
  if (plan.allUtxos.length === 0) {
    console.log("  (пусто)");
  } else {
    for (const u of plan.allUtxos) {
      const tag = u.dust ? "ПЫЛЬ" : !u.confirmed ? "НЕПОДТВ." : "OK";
      console.log(
        `  [${tag}] ${u.address.slice(0, 14)}… ${u.value} sats · fee≈${u.singleFee} · ${u.txid.slice(0, 10)}…:${u.vout}`,
      );
    }
  }

  console.log("\n  ── План пакета ──");
  console.log(`  Входов:          ${plan.spendable.length}`);
  console.log(`  Пропуск пыли:    ${plan.dustSkipped}`);
  console.log(`  Пропуск unconf:  ${plan.unconfirmedSkipped}${plan.unconfirmedSkipped ? " (добавьте --force)" : ""}`);
  console.log(`  Сумма входов:    ${plan.totalIn} sats (${satsToBtc(plan.totalIn)} BTC)`);
  console.log(`  vBytes:          ${plan.vbytes}`);
  console.log(`  Комиссия пакета: ${plan.feeSats} sats (${satsToBtc(plan.feeSats)} BTC)`);
  console.log(`  На Vault (net):  ${plan.net} sats (${satsToBtc(plan.net)} BTC)`);
  console.log(`  Рентабельно:     ${plan.profitable ? "ДА ✓" : "НЕТ ✗"}`);
  console.log("");
}

module.exports = {
  loadEnvFiles,
  getConfig,
  auditSweepPlan,
  assertProfitablePlan,
  buildSignedTransaction,
  broadcastSignedTx,
  printAuditReport,
  satsToBtc,
  ROOT,
};
