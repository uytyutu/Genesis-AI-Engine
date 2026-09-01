# COMPUTE ENGINE AUDIT → V1

Дата: 2026-08-31 · **NO COMMIT / NO PUSH**

## AUDIT (до кода)

| Вопрос | Факт |
|--------|------|
| Существовал ли mining/PoUW модуль? | Нет (только Farm money_hunter / Opire — другой трек) |
| Переписывать коммерческий Virtus? | Нет — отдельный `virtus_core/compute_engine/` |
| Windows + Golem? | SKIPPED (нужен Linux+KVM) |
| GTX 1650 + BTC SHA-256? | Измеримо, экономически ≈0 share сети |

## AVAILABLE HARDWARE (live)

- CPU: Intel i5-10300H · 4c/8t · RAM 31.8 GB
- GPU: **NVIDIA GeForce GTX 1650** · 4096 MiB · ~5–6 W idle · CUDA in-process: **False** (нет torch в runtime)

## MEASURED BENCHMARKS

- sha256d_cpu ≈ **373k H/s**
- blake2b_cpu ≈ **932k H/s**
- measure worker: REAL_REWARD = **0**

## POSSIBLE PROTOCOLS

| ID | Status |
|----|--------|
| local_sha256_measure | VERIFIED (reward 0) |
| btc_sha256 | BENCHMARKED / DISABLED for profit |
| flux_pouw | DISCOVERED |
| golem_provider | SKIPPED |
| gpu_pow_generic | DISCOVERED |

## MISSING DEPENDENCIES / BLOCKERS

1. `VIRTUS_ELECTRICITY_EUR_PER_KWH` не задан → EUR NET = UNKNOWN  
2. Нет VERIFIED GPU miner / CUDA adapter  
3. Нет Live Earn connector → Treasury CONFIRMED = 0  
4. Golem не zero-setup на этой машине  

## EXPECTED IMPLEMENTATION (сделано V1)

- Hardware detector (nvidia-smi + CIM)  
- Local benchmarks  
- Opportunity scanner + profitability (honest)  
- Worker manager (measure only)  
- Payout ledger states EXPECTED/PENDING/CONFIRMED/WITHDRAWABLE  
- Experiment ledger baseline  
- CLI + `/compute` UI + `/api/compute/*`  

## CONCLUSION

**NO PROFITABLE COMPUTE FOUND** — корректный результат V1.

Первый «успех» позже: внешний CONFIRMED payout → REAL treasury > 0.
