# RALG Customer Demo

This five-minute local demo shows document ingestion, a grounded answer with
evidence, and safe abstention when the document does not contain the answer.

## Start the API

```powershell
.venv\Scripts\python.exe -m uvicorn src.api_server:app --host 127.0.0.1 --port 8000
```

## 1. Ingest a document

```powershell
$document = @'
LUMEN ARC-12 VACUUM KILN STARTUP CARD. Set chamber purge pressure to 3.7 bar.
Use only Vireo-22 coolant. Before opening the service hatch, isolate disconnect
K-41 and verify zero voltage at terminal J3.
For an amber FEED-LOW alarm, inspect screen F-9 and verify valve V-12 is fully open.
'@

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/ingest `
  -ContentType application/json `
  -Body (@{text=$document; document_name='lumen_arc12_startup'} | ConvertTo-Json)
```

## 2. Ask a supported question

```powershell
$supported = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/query `
  -ContentType application/json `
  -Body (@{question='What should be checked for an amber FEED-LOW alarm?'; top_k=5; include_sources=$true} | ConvertTo-Json)
$supported | ConvertTo-Json -Depth 5
```

Confirm that `supported` is true, the answer contains `F-9` and `V-12`, and `sources`
contains the ingested card. The source preview and score are the cited evidence;
the answer should not be accepted as grounded without them.

## 3. Ask an unsupported question

```powershell
$unsupported = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/query `
  -ContentType application/json `
  -Body (@{question='How long is the ARC-12 warranty?'; top_k=5; include_sources=$true} | ConvertTo-Json)
$unsupported | ConvertTo-Json -Depth 5
```

Confirm that `supported` is false and the response states that there is not
enough reliable evidence. This is the expected safe-abstention behavior.

## Reproduce the held-out checkpoint

The automated checkpoint ingests three independent ARC-12 service cards and
evaluates supported and unsupported questions:

```powershell
.venv\Scripts\python.exe scripts\run_commercial_validation.py
```

Machine-readable results are written to
`logs/heldout_commercial_v1_results.json`.
