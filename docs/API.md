# API reference

Run RelayGuard and open `/docs` for the generated FastAPI interface. All routes share the website's origin. This API has no authentication; keep it local or behind the SSH tunnel.

| Method | Path | Behavior |
| :--- | :--- | :--- |
| GET | `/api/health` | Status, model version, architecture, system, source |
| GET | `/api/state` | Latest 1,000 events, total counts, policy, reports, runtime |
| POST | `/api/replay` | Score next test payment; `done: true` when exhausted |
| POST | `/api/score` | Score a manual payment |
| GET | `/api/explain/{id}` | Compute/retrieve grouped attribution |
| POST | `/api/review/{id}` | Save review and note |
| POST | `/api/settings` | Set threshold for future events |
| GET | `/api/export` | Active event/review CSV |
| GET | `/api/export?archived=true` | Earlier model-version records |
| POST | `/api/reset` | Clear active events, restart replay |
| POST | `/api/train` | Multipart labeled CSV; replaces model, clears active events |

## Manual payment

Read `/api/state`; use a `step` at least as large as `last_step`. This sample illustrates the structure, not a guaranteed valid timeline or score:

```json
{
  "id": "MANUAL-0001",
  "step": 744,
  "type": "TRANSFER",
  "amount": 25000,
  "sender": "C-DEMO-SENDER",
  "recipient": "C-DEMO-RECIPIENT"
}
```

POST to `/api/score`. IDs must be unique; amount positive and finite; step non-negative and chronological; sender/recipient non-empty and different. Valid types: PAYMENT, TRANSFER, CASH_OUT, CASH_IN, DEBIT. PaySim nameOrig/nameDest aliases are accepted.

Responses include payment fields, `score`, `flagged`, `threshold`, `reasons`, `review`, `note`, `origin`, `version`, `context_source`, and `latency_ms`. Private feature snapshots, fingerprints, and ground-truth labels are omitted from public events.

## Review and settings

POST `/api/review/MANUAL-0001`:

```json
{"review": "Needs investigation", "note": "Verify the recipient."}
```

Valid statuses: Needs investigation, Dismissed, Unreviewed. Notes are stored up to 1,000 characters. This saves a decision and performs no banking operation.

POST `/api/settings`:

```json
{"threshold": 0.98}
```

Threshold must be strictly between 0 and 1. Old events retain their original flags and thresholds.

## Explanations

The response includes `method`, `baseline`, `score`, `threshold`, `contributions`, `reconstructed_score`, `reconciliation_error`, `summary`, `reference_count`, `model_version`, and limitations. Contributions explain the model relative to its training reference; they are not calibrated fraud probabilities. Missing snapshots or incompatible models produce errors.

## Training and operational notes

CSV training uses multipart field `file`, at most 40,000,000 bytes, 100–150,000 parsed rows, ten distinct steps, and both classes in every split. Semantic columns: step,type,amount,sender/nameOrig,recipient/nameDest,isFraud. It uses the generic 60/20/20 context trainer, not sequence-v4 archive training.

- Validation commonly returns HTTP 400; replay chronology and incompatible explanations return 409; missing records return 404.
- CSV exports neutralize leading spreadsheet formula characters in string fields.
- State returns the latest 1,000 events; total counts and active exports include the full active store. UI windows are smaller.
- History is stateful in one process. No multi-worker or multi-tenant guarantees are implemented.
- Health identifies architecture, not independent hosting-provider attestation.
