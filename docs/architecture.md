# Architecture

RALG is a retrieval-first local AI pipeline.

## High-level flow

```text
Question
  -> query planning
  -> retrieval
  -> evidence filtering
  -> route selection
  -> answer / reasoning path
  -> support check
  -> answer with evidence or abstention
```

## Main components

| Component | Role |
|---|---|
| Query planner | Builds retrieval queries from the user question |
| Retriever | Finds candidate evidence chunks from the knowledge base |
| Router | Chooses whether the question needs factual extraction, reasoning, or abstention logic |
| Reasoning model/path | Handles selected questions where lightweight reasoning is useful |
| Extractor | Produces grounded answers from retrieved support |
| Confidence/support logic | Decides whether the system should answer or abstain |
| Web UI | Provides an interactive Gradio interface |
| Evaluation suites | Test accuracy, support, false-premise rejection, and multi-hop behavior |

## Design constraints

The current design favors:

- local execution
- modest hardware
- evidence-grounded output
- limited extra retrieval passes
- simple dependencies
- repeatable evaluation

## Future architecture needs

- cleaner API layer
- separate public demo data from private/pilot data
- better benchmark runner
- deployment profiles for CPU and CUDA
- structured logs that avoid storing sensitive document text by default
