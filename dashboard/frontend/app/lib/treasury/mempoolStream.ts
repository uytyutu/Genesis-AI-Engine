/**
 * Real-time feeds for OWN tracked addresses.
 * BTC: mempool.space WebSocket · ETH: optional Alchemy/Infura WS (new heads → balance check).
 */
import { ethers } from "ethers";
import { resolveBtcAuditTargets, resolveEthAuditTargets } from "../../config/treasuryTargets";

export type StreamEvent =
  | { kind: "btc_tx"; address: string; txid: string; at: string }
  | { kind: "eth_activity"; address: string; blockNumber: number; balanceEth: number; at: string }
  | { kind: "status"; message: string; ok: boolean; at: string };

type Listener = (ev: StreamEvent) => void;

export class TreasuryMempoolStream {
  private listeners: Listener[] = [];
  private btcWs: WebSocket | null = null;
  private ethProvider: ethers.WebSocketProvider | null = null;
  private ethBlockHandler: ((n: number) => void) | null = null;
  private stopped = false;

  onEvent(fn: Listener) {
    this.listeners.push(fn);
    return () => {
      this.listeners = this.listeners.filter((l) => l !== fn);
    };
  }

  private emit(ev: StreamEvent) {
    for (const l of this.listeners) l(ev);
  }

  async start(extraEth: string[] = [], extraBtc: string[] = []) {
    this.stopped = false;
    this.startBtc(resolveBtcAuditTargets(extraBtc));
    await this.startEth(resolveEthAuditTargets(extraEth));
  }

  stop() {
    this.stopped = true;
    try {
      this.btcWs?.close();
    } catch {
      /* ignore */
    }
    this.btcWs = null;
    if (this.ethProvider && this.ethBlockHandler) {
      this.ethProvider.off("block", this.ethBlockHandler);
    }
    try {
      void this.ethProvider?.destroy();
    } catch {
      /* ignore */
    }
    this.ethProvider = null;
    this.ethBlockHandler = null;
  }

  private startBtc(addresses: string[]) {
    if (typeof window === "undefined" || addresses.length === 0) {
      this.emit({
        kind: "status",
        ok: true,
        message: "BTC WS: нет целей — пропуск.",
        at: new Date().toISOString(),
      });
      return;
    }
    const url = process.env.NEXT_PUBLIC_MEMPOOL_WS || "wss://mempool.space/api/v1/ws";
    try {
      const ws = new WebSocket(url);
      this.btcWs = ws;
      let lastTxEmit = 0;
      ws.onopen = () => {
        for (const a of addresses) {
          ws.send(JSON.stringify({ "track-address": a }));
        }
        this.emit({
          kind: "status",
          ok: true,
          message: `BTC mempool WS: ${addresses.length} адр.`,
          at: new Date().toISOString(),
        });
      };
      ws.onmessage = (msg) => {
        try {
          const data = JSON.parse(String(msg.data)) as Record<string, unknown>;
          const txid =
            (data["txid"] as string | undefined) ||
            (Array.isArray(data["address-transactions"])
              ? String((data["address-transactions"] as { txid?: string }[])[0]?.txid || "")
              : "");
          if (!txid) return;
          const now = Date.now();
          if (now - lastTxEmit < 15_000) return;
          lastTxEmit = now;
          const addr = (data["address-transactions"] || data["address"] || data["tracked-address"]) as
            | string
            | undefined;
          this.emit({
            kind: "btc_tx",
            address: String(addr || addresses[0]),
            txid,
            at: new Date().toISOString(),
          });
        } catch {
          /* ignore parse */
        }
      };
      ws.onerror = () => {
        this.emit({ kind: "status", ok: false, message: "BTC WS ошибка", at: new Date().toISOString() });
      };
      ws.onclose = () => {
        if (!this.stopped) {
          this.emit({ kind: "status", ok: false, message: "BTC WS закрыт", at: new Date().toISOString() });
        }
      };
    } catch (e) {
      this.emit({
        kind: "status",
        ok: false,
        message: e instanceof Error ? e.message : "BTC WS сбой",
        at: new Date().toISOString(),
      });
    }
  }

  private async startEth(addresses: string[]) {
    const wsUrl = process.env.NEXT_PUBLIC_ETH_WS_URL;
    if (!wsUrl || addresses.length === 0) {
      this.emit({
        kind: "status",
        ok: true,
        message: wsUrl
          ? "ETH WS: нет целей — пропуск."
          : "ETH WS выкл (задайте NEXT_PUBLIC_ETH_WS_URL при необходимости).",
        at: new Date().toISOString(),
      });
      return;
    }
    try {
      const provider = new ethers.WebSocketProvider(wsUrl);
      this.ethProvider = provider;
      const lastBal = new Map<string, string>();
      let lastEmit = 0;
      const onBlock = async (blockNumber: number) => {
        // Не чаще раза в 20 с — иначе вкладка зависает на каждом блоке
        const now = Date.now();
        if (now - lastEmit < 20_000) return;
        for (const address of addresses) {
          try {
            const bal = await provider.getBalance(address);
            const prev = lastBal.get(address.toLowerCase());
            const cur = bal.toString();
            if (prev !== undefined && prev !== cur) {
              lastEmit = now;
              this.emit({
                kind: "eth_activity",
                address,
                blockNumber,
                balanceEth: Number(ethers.formatEther(bal)),
                at: new Date().toISOString(),
              });
            }
            lastBal.set(address.toLowerCase(), cur);
          } catch {
            /* ignore single address */
          }
        }
      };
      this.ethBlockHandler = onBlock;
      provider.on("block", onBlock);
      this.emit({
        kind: "status",
        ok: true,
        message: `ETH WS: следим за ${addresses.length} адр.`,
        at: new Date().toISOString(),
      });
    } catch (e) {
      this.emit({
        kind: "status",
        ok: false,
        message: e instanceof Error ? e.message : "ETH WS ошибка",
        at: new Date().toISOString(),
      });
    }
  }
}
