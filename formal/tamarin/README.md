# Tamarin models (stub)

This directory holds **Tamarin** prover sketches for ledger hash-linking.
Stubs are documentation for formal-methods reviewers. They are not claimed to
be runnable without further work (lemma statements may need rewriting for a
specific Tamarin version).

| File | Intent |
| --- | --- |
| `ledger.spthy` | Hash-linked record chain: no fork, no gap, tip binds epoch |

Run (when the theory is completed):

```bash
tamarin-prover formal/tamarin/ledger.spthy
```

See also [`../tla/LedgerChain.tla`](../tla/LedgerChain.tla) for the TLC model
already in tree, and [`../PROPERTIES.md`](../PROPERTIES.md) for property IDs.
