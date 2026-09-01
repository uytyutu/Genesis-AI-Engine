/**
 * VCORE Genesis — TON testnet only.
 * Gate: Wallet → Deploy Jetton → Mint → Transfer → Verify on-chain.
 * NO LP. NO mainnet. Keys only from .env.ton (never in state JSON).
 */
"use strict";

const fs = require("fs");
const path = require("path");
const dotenv = require("dotenv");
const { mnemonicNew, mnemonicToPrivateKey } = require("@ton/crypto");
const { Address, toNano, internal } = require("@ton/core");
const { TonClient, WalletContractV4 } = require("@ton/ton");
const {
  AssetsSDK,
  createApi,
  NoopStorage,
  importKey,
} = require("@ton-community/assets-sdk");

const ROOT = path.resolve(__dirname, "..", "..");
const STATE_PATH = path.join(ROOT, ".runtime", "vcore_genesis_state.json");
const ENV_PATH = path.join(ROOT, ".env.ton");

const NETWORK = "testnet";
const SYMBOL = "VCORE";
const DECIMALS = 9;
const DEFAULT_SUPPLY = 1_000_000n;
const PROBE_WALLET_ID = 698983191 + 42;
const MIN_DEPLOY_TON = 1.2;

function emptyValueLayers(supplyHuman) {
  const declaredUsd = Number(supplyHuman); // reference $1 / VCORE — NOT executable
  return {
    declared: {
      label: "DECLARED VALUE",
      amount: declaredUsd,
      unit: "USD",
      note: "Reference only (1 VCORE = $1 model). Not money.",
    },
    model: {
      label: "MODEL VALUE",
      amount: declaredUsd,
      unit: "USD",
      model: "A_FIXED_EMISSION",
      note: "Model A — fixed emission reference. Not market, not settlement.",
    },
    market: {
      label: "MARKET VALUE",
      amount: 0,
      unit: "USD",
      note: "No public market / pool yet.",
    },
    executable: {
      label: "EXECUTABLE VALUE",
      amount: 0,
      unit: "TON",
      note: "Conversion Engine quote. 0 until pool + route.",
    },
    realSettlement: {
      label: "REALIZED VALUE",
      amount: 0,
      unit: "TON",
      tx: null,
      note: "Only after confirmed VCORE→TON (or other) swap. Forbidden to paint. Alias: REAL SETTLEMENT.",
    },
  };
}

function defaultState() {
  return {
    ok: true,
    network: "ton-testnet",
    symbol: SYMBOL,
    decimals: DECIMALS,
    supplyHuman: String(DEFAULT_SUPPLY),
    stage: "NOT_STARTED",
    status: "GENESIS_DRAFT",
    adminAddress: null,
    probeAddress: null,
    jettonMaster: null,
    jettonWalletAdmin: null,
    jettonWalletProbe: null,
    totalSupplyOnChain: null,
    adminBalanceOnChain: null,
    probeBalanceOnChain: null,
    deployAt: null,
    transferAt: null,
    verifiedAt: null,
    externalVerification: {
      status: "PENDING",
      identity: null,
      local: null,
      remote: null,
      mismatches: [],
      comparedAt: null,
      source: null,
    },
    explorer: {},
    faucetHint: "https://t.me/testgiver_ton_bot",
    gates: {
      lpAllowed: false,
      mainnetAllowed: false,
      researchOpen: false,
      conversionOpen: false,
      nextAfterGenesisPass: "dex_discovery",
    },
    valueLayers: emptyValueLayers(DEFAULT_SUPPLY),
    blockers: ["NO_WALLET"],
    log: [],
    updatedAt: null,
  };
}

function ensureRuntimeDir() {
  fs.mkdirSync(path.dirname(STATE_PATH), { recursive: true });
}

function loadState() {
  ensureRuntimeDir();
  if (!fs.existsSync(STATE_PATH)) return defaultState();
  try {
    return { ...defaultState(), ...JSON.parse(fs.readFileSync(STATE_PATH, "utf8")) };
  } catch {
    return defaultState();
  }
}

function saveState(state) {
  ensureRuntimeDir();
  state.updatedAt = new Date().toISOString();
  fs.writeFileSync(STATE_PATH, JSON.stringify(state, null, 2), "utf8");
  return state;
}

function pushLog(state, msg) {
  const line = `${new Date().toISOString()} · ${msg}`;
  state.log = [line, ...(state.log || [])].slice(0, 80);
  return line;
}

function loadEnv() {
  if (fs.existsSync(ENV_PATH)) dotenv.config({ path: ENV_PATH });
  dotenv.config({ path: path.join(ROOT, ".env") });
}

function parseMnemonic() {
  loadEnv();
  const raw = (process.env.TON_MNEMONIC || "").trim();
  if (!raw) return null;
  return raw.split(/\s+/).filter(Boolean);
}

function tonClient() {
  loadEnv();
  const key = (process.env.TONCENTER_API_KEY || "").trim();
  return new TonClient({
    endpoint: "https://testnet.toncenter.com/api/v2/jsonRPC",
    apiKey: key || undefined,
  });
}

function walletsFromKey(keyPair) {
  const admin = WalletContractV4.create({ workchain: 0, publicKey: keyPair.publicKey });
  const probe = WalletContractV4.create({
    workchain: 0,
    publicKey: keyPair.publicKey,
    walletId: PROBE_WALLET_ID,
  });
  return { admin, probe };
}

function makeSender(client, keyPair, wallet) {
  const opened = client.open(wallet);
  return {
    address: wallet.address,
    send: async (args) => {
      const seqno = await opened.getSeqno();
      await opened.sendTransfer({
        seqno,
        secretKey: keyPair.secretKey,
        messages: [
          internal({
            to: args.to,
            value: args.value,
            body: args.body,
            bounce: args.bounce ?? true,
            init: args.init,
          }),
        ],
      });
    },
  };
}

function explorerMaster(addr) {
  return `https://testnet.tonviewer.com/${addr}`;
}

function unitsFromHuman(human, decimals = DECIMALS) {
  const n = BigInt(String(human).replace(/_/g, ""));
  let scale = 1n;
  for (let i = 0; i < decimals; i++) scale *= 10n;
  return n * scale;
}

function humanFromUnits(units, decimals = DECIMALS) {
  const u = BigInt(units);
  let scale = 1n;
  for (let i = 0; i < decimals; i++) scale *= 10n;
  const whole = u / scale;
  const frac = u % scale;
  if (frac === 0n) return whole.toString();
  const fracStr = frac.toString().padStart(decimals, "0").replace(/0+$/, "");
  return `${whole}.${fracStr}`;
}

async function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function waitForActive(client, address, tries = 30) {
  for (let i = 0; i < tries; i++) {
    try {
      if (await client.isContractDeployed(address)) return true;
    } catch {
      /* retry */
    }
    await sleep(2000);
  }
  return false;
}

/**
 * INIT — create mnemonic if missing, register admin+probe addresses, stop at faucet.
 */
async function genesisInit({ forceNewMnemonic = false } = {}) {
  const state = loadState();
  loadEnv();

  let words = parseMnemonic();
  if (!words || forceNewMnemonic) {
    words = await mnemonicNew(24);
    const body = [
      "# Virtus VCORE Genesis — TON TESTNET ONLY",
      "# NEVER commit. NEVER mainnet until Owner gate.",
      "# Faucet: https://t.me/testgiver_ton_bot",
      "",
      `TON_NETWORK=testnet`,
      `TON_MNEMONIC=${words.join(" ")}`,
      "# TONCENTER_API_KEY=",
      `VCORE_SUPPLY=${DEFAULT_SUPPLY}`,
      "",
    ].join("\n");
    fs.writeFileSync(ENV_PATH, body, "utf8");
    pushLog(state, "Created .env.ton with new 24-word mnemonic (local only)");
  }

  const keyPair = await mnemonicToPrivateKey(words);
  const { admin, probe } = walletsFromKey(keyPair);
  const client = tonClient();
  let balanceNano = 0n;
  try {
    balanceNano = await client.getBalance(admin.address);
  } catch (e) {
    pushLog(state, `Balance fetch warning: ${e.message || e}`);
  }
  const tonBal = Number(balanceNano) / 1e9;

  state.adminAddress = admin.address.toString({ bounceable: false, testOnly: true });
  state.probeAddress = probe.address.toString({ bounceable: false, testOnly: true });
  state.supplyHuman = String(process.env.VCORE_SUPPLY || DEFAULT_SUPPLY);
  state.valueLayers = emptyValueLayers(BigInt(state.supplyHuman));
  state.explorer.admin = explorerMaster(state.adminAddress);
  state.explorer.probe = explorerMaster(state.probeAddress);

  if (tonBal < MIN_DEPLOY_TON) {
    state.stage = "WAITING_FAUCET";
    state.status = "GENESIS_DRAFT";
    state.blockers = ["WAITING_FAUCET"];
    pushLog(
      state,
      `Admin ${state.adminAddress} balance=${tonBal.toFixed(4)} testnet TON — need ≥ ${MIN_DEPLOY_TON}. Faucet: ${state.faucetHint}`,
    );
  } else {
    state.stage = "FUNDED";
    state.status = "GENESIS_DRAFT";
    state.blockers = [];
    pushLog(state, `Admin funded: ${tonBal.toFixed(4)} testnet TON — ready to deploy`);
  }

  saveState(state);
  freezeRealityLedger();
  return {
    ...state,
    tonBalance: tonBal,
    mnemonicWritten: !parseMnemonic() || forceNewMnemonic ? undefined : false,
    envPath: ENV_PATH,
    next:
      tonBal < MIN_DEPLOY_TON
        ? `Fund admin via faucet, then: npm run vcore:genesis:deploy`
        : `npm run vcore:genesis:deploy`,
  };
}

/**
 * DEPLOY + PREMINT on testnet (no LP).
 */
async function genesisDeploy() {
  const state = loadState();
  const words = parseMnemonic();
  if (!words) {
    throw new Error("No TON_MNEMONIC — run npm run vcore:genesis:init first");
  }

  const keyPair = await importKey(words);
  const { admin, probe } = walletsFromKey(keyPair);
  const client = tonClient();
  const balanceNano = await client.getBalance(admin.address);
  const tonBal = Number(balanceNano) / 1e9;
  if (tonBal < MIN_DEPLOY_TON) {
    state.stage = "WAITING_FAUCET";
    state.blockers = ["WAITING_FAUCET"];
    pushLog(state, `Deploy blocked: balance ${tonBal} < ${MIN_DEPLOY_TON}`);
    saveState(state);
    return { ...state, tonBalance: tonBal, error: "WAITING_FAUCET" };
  }

  const supplyHuman = BigInt(process.env.VCORE_SUPPLY || state.supplyHuman || DEFAULT_SUPPLY);
  const premint = unitsFromHuman(supplyHuman, DECIMALS);

  pushLog(state, `Deploying VCORE Jetton on ${NETWORK} supply=${supplyHuman}…`);
  saveState(state);

  const api = await createApi(NETWORK);
  const sender = makeSender(client, keyPair, admin);
  const sdk = AssetsSDK.create({
    api,
    sender,
    storage: new NoopStorage(),
  });

  const jetton = await sdk.deployJetton(
    {
      name: "Virtus Core",
      symbol: SYMBOL,
      decimals: DECIMALS,
      description:
        "Virtus Core Genesis testnet Jetton — experiment only. Not mainnet. Not backed by Toloka spend.",
    },
    {
      onchainContent: true,
      premintAmount: premint,
      value: toNano("0.25"),
      premintOptions: {
        notify: true,
      },
    },
  );

  const master = jetton.address.toString();
  state.jettonMaster = master;
  state.adminAddress = admin.address.toString({ bounceable: false, testOnly: true });
  state.probeAddress = probe.address.toString({ bounceable: false, testOnly: true });
  state.supplyHuman = String(supplyHuman);
  state.deployAt = new Date().toISOString();
  state.stage = "DEPLOYED";
  state.status = "DEPLOYED_TESTNET";
  state.explorer.master = explorerMaster(master);
  state.blockers = ["AWAITING_CONFIRM"];
  pushLog(state, `Deploy+premint sent. Master=${master}`);
  saveState(state);

  const active = await waitForActive(client, jetton.address, 40);
  if (!active) {
    pushLog(state, "Master not active yet — run verify later");
    state.blockers = ["AWAITING_CONFIRM"];
    saveState(state);
    return state;
  }

  // refresh via AssetsSDK open
  const opened = sdk.openJetton(jetton.address);
  let data;
  for (let i = 0; i < 20; i++) {
    try {
      data = await opened.getData();
      break;
    } catch {
      await sleep(2000);
    }
  }
  if (data) {
    state.totalSupplyOnChain = humanFromUnits(data.totalSupply);
    const jw = await opened.getWalletAddress(admin.address);
    state.jettonWalletAdmin = jw.toString();
    state.explorer.jettonWalletAdmin = explorerMaster(state.jettonWalletAdmin);
    state.stage = "MINTED";
    state.blockers = [];
    pushLog(state, `On-chain supply=${state.totalSupplyOnChain} VCORE · JW admin=${state.jettonWalletAdmin}`);
  }

  state.valueLayers = emptyValueLayers(supplyHuman);
  saveState(state);
  return state;
}

/**
 * TRANSFER small amount admin → probe (proves jetton wallet path).
 */
async function genesisTransfer({ amountHuman = "1000" } = {}) {
  const state = loadState();
  if (!state.jettonMaster) throw new Error("No jettonMaster — deploy first");
  const words = parseMnemonic();
  if (!words) throw new Error("No TON_MNEMONIC");

  const keyPair = await importKey(words);
  const { admin, probe } = walletsFromKey(keyPair);
  const client = tonClient();
  const api = await createApi(NETWORK);
  const sender = makeSender(client, keyPair, admin);
  const sdk = AssetsSDK.create({ api, sender, storage: new NoopStorage() });
  const master = sdk.openJetton(Address.parse(state.jettonMaster));

  const amount = unitsFromHuman(amountHuman, DECIMALS);
  const adminJw = await master.getWallet(admin.address);

  pushLog(state, `Transfer ${amountHuman} VCORE → probe ${probe.address.toString({ testOnly: true })}`);
  await adminJw.send(sender, probe.address, amount, {
    notify: true,
    value: toNano("0.08"),
  });

  state.transferAt = new Date().toISOString();
  state.stage = "TRANSFERRED";
  state.blockers = ["AWAITING_TRANSFER_CONFIRM"];
  saveState(state);

  await sleep(8000);
  return genesisVerify();
}

function freezeRealityLedger() {
  const ledgerPath = path.join(ROOT, ".runtime", "vcore_reality_ledger.json");
  ensureRuntimeDir();
  let prev = {};
  try {
    if (fs.existsSync(ledgerPath)) prev = JSON.parse(fs.readFileSync(ledgerPath, "utf8"));
  } catch {
    prev = {};
  }
  const frozen = {
    model: {
      usd: Number(prev?.model?.usd || DEFAULT_SUPPLY),
      note: "DECLARED/MODEL reference only — not cash.",
    },
    real: {
      ton: 0,
      btc: 0,
      note: "FROZEN at 0 until confirmed external TON/BTC receipt. Creating VCORE does NOT increase REAL.",
    },
    transactions: Array.isArray(prev.transactions) ? prev.transactions : [],
    frozen: true,
    law: "VCORE mint ≠ REAL TON/BTC. REAL ledger stays 0 through Genesis.",
    updatedAt: new Date().toISOString(),
  };
  // Hard freeze — never allow accidental paint
  frozen.real.ton = 0;
  frozen.real.btc = 0;
  fs.writeFileSync(ledgerPath, JSON.stringify(frozen, null, 2), "utf8");
  return frozen;
}

/**
 * EXTERNAL VERIFICATION — independent TonClient/RPC read vs Virtus local state.
 * Never trust DB alone for IDENTITY VERIFIED.
 */
async function externalVerifyAgainstChain(state) {
  const localMaster = state.jettonMaster;
  const result = {
    status: "PENDING",
    identity: null,
    local: {
      jettonMaster: localMaster,
      totalSupplyOnChain: state.totalSupplyOnChain,
      adminBalanceOnChain: state.adminBalanceOnChain,
      probeBalanceOnChain: state.probeBalanceOnChain,
      supplyHuman: state.supplyHuman,
    },
    remote: null,
    mismatches: [],
    comparedAt: new Date().toISOString(),
    source: "toncenter-testnet + AssetsSDK getData (independent open)",
  };

  if (!localMaster) {
    result.status = "IDENTITY_MISMATCH";
    result.identity = "IDENTITY_MISMATCH";
    result.mismatches.push("NO_LOCAL_MASTER");
    return result;
  }

  const client = tonClient();
  const masterAddr = Address.parse(localMaster);

  let deployed = false;
  try {
    deployed = await client.isContractDeployed(masterAddr);
  } catch (e) {
    result.mismatches.push(`RPC_DEPLOY_CHECK_FAIL:${e.message || e}`);
  }

  // Second independent open via createApi (not reading from Virtus cache)
  let remoteSupply = null;
  let remoteAdminBal = null;
  let remoteProbeBal = null;
  try {
    const api = await createApi(NETWORK);
    const sdk = AssetsSDK.create({ api, storage: new NoopStorage() });
    const opened = sdk.openJetton(masterAddr);
    const data = await opened.getData();
    remoteSupply = humanFromUnits(data.totalSupply);

    const words = parseMnemonic();
    if (words) {
      const keyPair = await importKey(words);
      const { admin, probe } = walletsFromKey(keyPair);
      try {
        const jwA = await opened.getWallet(admin.address);
        remoteAdminBal = humanFromUnits((await jwA.getData()).balance);
      } catch {
        /* optional */
      }
      try {
        const jwP = await opened.getWallet(probe.address);
        remoteProbeBal = humanFromUnits((await jwP.getData()).balance);
      } catch {
        /* optional */
      }
    }
  } catch (e) {
    result.mismatches.push(`RPC_GETDATA_FAIL:${e.message || e}`);
  }

  result.remote = {
    contractDeployed: deployed,
    totalSupplyOnChain: remoteSupply,
    adminBalanceOnChain: remoteAdminBal,
    probeBalanceOnChain: remoteProbeBal,
    master: localMaster,
  };

  if (!deployed) result.mismatches.push("MASTER_NOT_DEPLOYED_ON_CHAIN");
  if (remoteSupply == null) result.mismatches.push("REMOTE_SUPPLY_UNREADABLE");
  else if (String(state.totalSupplyOnChain) !== String(remoteSupply)) {
    // Allow local still null on first verify — then sync from remote
    if (state.totalSupplyOnChain != null && state.totalSupplyOnChain !== remoteSupply) {
      result.mismatches.push(
        `SUPPLY_MISMATCH local=${state.totalSupplyOnChain} remote=${remoteSupply}`,
      );
    }
  }
  if (
    state.adminBalanceOnChain != null &&
    remoteAdminBal != null &&
    String(state.adminBalanceOnChain) !== String(remoteAdminBal)
  ) {
    result.mismatches.push(
      `ADMIN_BAL_MISMATCH local=${state.adminBalanceOnChain} remote=${remoteAdminBal}`,
    );
  }
  if (
    state.probeBalanceOnChain != null &&
    remoteProbeBal != null &&
    String(state.probeBalanceOnChain) !== String(remoteProbeBal)
  ) {
    result.mismatches.push(
      `PROBE_BAL_MISMATCH local=${state.probeBalanceOnChain} remote=${remoteProbeBal}`,
    );
  }

  // Expected supply from declared mint
  if (remoteSupply != null) {
    const expected = String(state.supplyHuman || DEFAULT_SUPPLY);
    const remoteWhole = String(remoteSupply).split(".")[0];
    if (remoteWhole !== expected && remoteSupply !== expected) {
      // not hard fail if transfer moved tokens — total supply should still match mint
      if (remoteWhole !== expected) {
        result.mismatches.push(`SUPPLY_NE_DECLARED remote=${remoteSupply} declared=${expected}`);
      }
    }
  }

  if (result.mismatches.length === 0 && deployed && remoteSupply != null) {
    result.status = "IDENTITY_VERIFIED";
    result.identity = "IDENTITY_VERIFIED";
  } else {
    result.status = "IDENTITY_MISMATCH";
    result.identity = "IDENTITY_MISMATCH";
  }
  return result;
}

/**
 * VERIFY — read chain; EXTERNAL VERIFICATION required for IDENTITY VERIFIED.
 * REAL ledger stays frozen at 0 (VCORE ≠ TON).
 */
async function genesisVerify() {
  const state = loadState();
  freezeRealityLedger();

  if (!state.jettonMaster) {
    state.blockers = ["NO_JETTON_MASTER"];
    state.status = "GENESIS_DRAFT";
    state.externalVerification = {
      status: "PENDING",
      identity: null,
      local: null,
      remote: null,
      mismatches: ["NO_JETTON_MASTER"],
      comparedAt: new Date().toISOString(),
      source: null,
    };
    pushLog(state, "Verify: no master address in state");
    saveState(state);
    return state;
  }

  const api = await createApi(NETWORK);
  const sdk = AssetsSDK.create({ api, storage: new NoopStorage() });
  const master = sdk.openJetton(Address.parse(state.jettonMaster));

  let data;
  try {
    data = await master.getData();
  } catch (e) {
    state.blockers = ["CHAIN_READ_FAIL"];
    pushLog(state, `Verify getData failed: ${e.message || e}`);
    saveState(state);
    return state;
  }

  state.totalSupplyOnChain = humanFromUnits(data.totalSupply);
  state.status = "DEPLOYED_TESTNET";
  state.explorer.master = explorerMaster(state.jettonMaster);

  const words = parseMnemonic();
  if (words) {
    const keyPair = await importKey(words);
    const { admin, probe } = walletsFromKey(keyPair);
    state.adminAddress = admin.address.toString({ bounceable: false, testOnly: true });
    state.probeAddress = probe.address.toString({ bounceable: false, testOnly: true });
    try {
      const jwA = await master.getWallet(admin.address);
      const balA = await jwA.getData();
      state.jettonWalletAdmin = jwA.address.toString();
      state.adminBalanceOnChain = humanFromUnits(balA.balance);
    } catch (e) {
      pushLog(state, `Admin JW: ${e.message || e}`);
    }
    try {
      const jwP = await master.getWallet(probe.address);
      const balP = await jwP.getData();
      state.jettonWalletProbe = jwP.address.toString();
      state.probeBalanceOnChain = humanFromUnits(balP.balance);
      state.explorer.jettonWalletProbe = explorerMaster(state.jettonWalletProbe);
    } catch (e) {
      pushLog(state, `Probe JW (may be undeployed until transfer): ${e.message || e}`);
    }
  }

  // Independent re-read + compare
  const ext = await externalVerifyAgainstChain(state);
  state.externalVerification = ext;
  if (ext.remote?.totalSupplyOnChain) {
    state.totalSupplyOnChain = ext.remote.totalSupplyOnChain;
  }
  if (ext.remote?.adminBalanceOnChain != null) {
    state.adminBalanceOnChain = ext.remote.adminBalanceOnChain;
  }
  if (ext.remote?.probeBalanceOnChain != null) {
    state.probeBalanceOnChain = ext.remote.probeBalanceOnChain;
  }

  const supplyOk = state.totalSupplyOnChain && BigInt(String(state.totalSupplyOnChain).split(".")[0]) > 0n;
  const transferOk =
    state.probeBalanceOnChain != null && Number(state.probeBalanceOnChain) > 0;
  const identityOk = ext.identity === "IDENTITY_VERIFIED";

  if (ext.identity === "IDENTITY_MISMATCH") {
    state.blockers = ["IDENTITY_MISMATCH", ...ext.mismatches];
    state.gates = {
      lpAllowed: false,
      mainnetAllowed: false,
      researchOpen: false,
      conversionOpen: false,
      killSwitch: true,
      nextAfterGenesisPass: "dex_discovery",
    };
    pushLog(state, `IDENTITY MISMATCH → KILL SWITCH · ${ext.mismatches.join("; ")}`);
  } else if (supplyOk && transferOk && identityOk) {
    state.stage = "VERIFIED";
    state.verifiedAt = new Date().toISOString();
    state.blockers = [];
    state.gates = {
      lpAllowed: false,
      mainnetAllowed: false,
      researchOpen: false,
      conversionOpen: false,
      nextAfterGenesisPass: "dex_discovery",
      genesisPass: true,
    };
    pushLog(
      state,
      `VERIFIED + EXTERNAL IDENTITY VERIFIED · supply=${state.totalSupplyOnChain} · admin=${state.adminBalanceOnChain} · probe=${state.probeBalanceOnChain} · REAL ledger still 0`,
    );
  } else if (supplyOk) {
    state.stage = "MINTED";
    state.blockers = transferOk ? [] : ["TRANSFER_NOT_CONFIRMED"];
    if (!identityOk) state.blockers.push("EXTERNAL_VERIFY_PENDING_OR_FAIL");
    pushLog(state, `Mint OK · transfer ${transferOk ? "OK" : "pending"} — next: npm run vcore:genesis:transfer`);
  } else {
    state.blockers = ["SUPPLY_ZERO_OR_UNREADABLE"];
  }

  // Value layers stay honest — identity ≠ executable TON; REALIZED stays 0
  const supplyHuman = BigInt(state.supplyHuman || DEFAULT_SUPPLY);
  state.valueLayers = emptyValueLayers(supplyHuman);
  state.valueLayers.realSettlement.amount = 0;
  state.valueLayers.realSettlement.tx = null;
  freezeRealityLedger();
  saveState(state);
  return state;
}

async function genesisStatus() {
  const state = loadState();
  const words = parseMnemonic();
  let tonBalance = null;
  if (words && state.adminAddress) {
    try {
      const client = tonClient();
      const { admin } = walletsFromKey(await mnemonicToPrivateKey(words));
      tonBalance = Number(await client.getBalance(admin.address)) / 1e9;
    } catch {
      /* ignore */
    }
  }
  return {
    ...state,
    tonBalance,
    hasMnemonic: !!words,
    statePath: STATE_PATH,
    law: "MODEL/DECLARED ≠ EXECUTABLE ≠ REAL. LP gate closed until Owner opens next brick.",
  };
}

module.exports = {
  STATE_PATH,
  ENV_PATH,
  loadState,
  saveState,
  genesisInit,
  genesisDeploy,
  genesisTransfer,
  genesisVerify,
  genesisStatus,
  emptyValueLayers,
  freezeRealityLedger,
  externalVerifyAgainstChain,
};
