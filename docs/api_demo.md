# API Demo Contract

This is the proposed developer-facing API shape for RALG Engine.

The current web UI is useful for manual demos, but pilots and technical buyers need an API contract so the engine can be tested from scripts and internal tools.

## Endpoint

```http
POST /query
Content-Type: application/json
```

## Request

```json
{
  "question": "What should a technician check before restarting the compressor?",
  "top_k": 5,
  "include_sources": true
}
```

## Response

```json
{
  "answer": "The technician should inspect the intake filter and confirm cooling airflow before restarting.",
  "supported": true,
  "confidence": 0.87,
  "answer_type": "factual",
  "sources": [
    {
      "rank": 1,
      "chunk_id": 142,
      "score": 18.4,
      "preview": "..."
    }
  ],
  "latency_ms": 421
}
```

## Curl example

```bash
curl -X POST http://localhost:7860/query \
  -H "Content-Type: application/json" \
  -d "{"question":"What safety step is required before opening the panel?","top_k":5}"
```

## Implementation target

The first API implementation should:

- reuse `rag_chat_v2.initialize_pipeline`
- reuse `rag_chat_v2.answer_question`
- return answer, supported flag, confidence, answer type, latency, and sources
- avoid logging full private document text by default
- work locally without cloud APIs

## Acceptance test

A developer should be able to:

1. start the app locally
2. send a JSON request
3. receive a cited answer or abstention
4. reproduce the same result with the same corpus and commit
