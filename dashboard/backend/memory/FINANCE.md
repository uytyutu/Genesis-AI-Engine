# Finance display cache (not a wallet)

Genesis **does not store money**. These files are a **read-only display cache** synced from Payment Hub / external provider.

| File | Purpose |
|------|---------|
| `finance_config.json` | Connected provider (`stripe`, etc.) and last sync time |
| `finance_snapshot.json` | Balances, revenue, expenses — mirrored from provider |
| `finance_transactions.jsonl` | Recent transactions for Finance Center UI |

When no provider is connected, the UI shows `0 €` and explains that data will appear after Payment Hub setup.
