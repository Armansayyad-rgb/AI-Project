# AI Project — Development README

## 1. Project Goal

We are building a local AI/RAG reasoning system that can:

- retrieve relevant knowledge from a large local corpus
- classify question intent
- answer supported questions with the correct answer type
- reject unsupported or false-premise questions
- handle causal, change, effect, structure, summary, significance, feature, entity-list, comparison, adversarial, and negative cases
- run on CUDA with a custom local reasoning model
- eventually become production-ready and commercially valuable

The long-term commercial goal is not just to have code that works, but to build a system with:

- strong independent benchmark results
- reliable false-premise rejection
- robust retrieval and routing
- portable deployment
- clean documentation
- reproducible setup
- a usable interface/API
- evidence of real-world value

---

## 2. Current Architecture

Main components currently involved include:

- `rag_chat_v2.py` — main RAG orchestration and answer pipeline
- `query_planner_v1.py` — intent detection, subject extraction, canonicalization, and query expansion
- `comparison_planner_v1.py` — comparison-specific planning
- `retriever_v2.py` / `retriever_v4.py` — retrieval
- `router_v1.py` — legacy routing
- `reasoning_confidence_v1.py` / `confidence_v1.py` — confidence logic
- `model_v2.py` — current reasoning model
- synthesizer modules — answer generation by type
- `evaluation_suite_v3.py` — main evaluation suite
- regression tests — additional stability checks

Knowledge currently loaded:

- `wikitext_v2.txt`
- `knowledge_extra_v1.txt`

Current knowledge size observed in evaluation:

- 107,650 chunks

Current device:

- CUDA

---

## 3. What Has Been Completed

### Core system

Completed:

- local model loads successfully
- CUDA execution works
- lexical knowledge index builds
- retrieval pipeline works
- routing pipeline works
- semantic query planner exists
- comparison planner exists
- canonical-question generation exists
- answer synthesizers exist
- evaluation suite v3 runs end-to-end

### Strong evaluation areas

Recent evaluation runs showed 100% in several categories, including:

- causal — reached 100% in at least one recent run
- effect — reached 100% after planner/RAG fixes
- comparison — 100%
- entity list — 100%
- features — 100%
- significance — 100%
- summary — 100%
- unsupported — 100%
- false claim — 100%
- adversarial — 100%

### False-premise work

A major false-premise bug was found where impossible relations such as:

- photosynthesis creating Roman law
- chromosomes limiting royal power
- DNA leading French revolutionary armies
- Robespierre producing haploid cells
- photosynthesis organizing the Roman Senate

were being answered instead of rejected.

We added asserted-relation detection and an early premise-validation gate in `rag_chat_v2.py`.

We then fixed missing relation patterns for:

- `What caused X to overthrow Y?`
- `Why did X divide Y?`
- other divide/split variants

The targeted false-premise test now correctly returns:

- `answer_type = system`
- `supported = False`
- no supporting sentence
- system rejection:
  `I couldn't find enough reliable evidence in the current knowledge base.`

This was verified manually on seven previously problematic questions.

### Comparison planner work

Comparison detection and extraction were expanded to handle forms such as:

- Explain the differences between X and Y
- Describe how X differs from Y
- In what ways are X and Y different
- What distinguishes X from Y
- How do X and Y differ
- What differentiates X from Y
- X versus Y
- X vs Y

These now correctly build comparison plans.

### Query planner work

The planner was expanded for:

- causal paraphrases
- change-over-time questions
- effect/aftermath questions
- structure questions
- process questions
- significance questions
- feature questions
- entity-list questions
- comparison questions

Special retrieval expansions were added for:

- Roman Empire decline
- Roman Empire aftermath
- Roman military / legion structure
- DNA structure
- photosynthesis
- Magna Carta significance
- French Revolution figures
- Roman Republic features

---

## 4. Latest Known Evaluation State

Before the newest false-premise patch, one recent V3 run achieved approximately:

- Semantic accuracy: 94.7%
- Answer-type accuracy: 96.7%
- Support-state accuracy: 97.1%
- Content accuracy: 95.1%
- Supported acceptance: 100%
- False-premise rejection: 91.2%

At that point:

- answer-type target passed
- support-state target passed
- supported-acceptance target passed
- semantic target narrowly missed
- false-premise target missed

Important: those numbers are now stale because the false-premise detector has since been improved.

A new `evaluation_suite_v3.py` run is currently being executed and should become the new baseline.

---

## 5. Known Remaining Problems

### A. Roman Empire change question

Known failure:

`Explain how the Roman Empire changed over time.`

Observed bad canonical form in one run:

`Explain how how the Roman Empire changed over time works.`

This indicates an intent/planner or canonicalization path is still sometimes routing a change question through process-style wording.

Need to verify whether the newest code still has this issue.

### B. Roman military structure content

Several structure questions are correctly classified as `structure`, but the answer often misses the required word/concept:

`cohort`

Examples:

- How was the Roman military organized?
- How were Roman legions organized?
- What units formed a Roman legion?
- Describe the internal structure of a Roman legion.
- How were Roman soldiers organized into units?

The problem is no longer mainly intent detection.

The remaining issue is likely:

- retrieval ranking
- context selection
- synthesizer sentence selection
- evidence weighting

Need to inspect retrieved chunks and make sure cohort-containing evidence wins.

### C. Internal canonical strings for false premises

False-premise rejection now works, but internal planning still produces ugly canonical questions such as:

`Why did Why did photosynthesis create Roman law decline?`

This is currently harmless because the asserted-relation gate rejects the question before generation, but it should still be cleaned up later for architecture quality.

### D. Deployment/engineering debt

Still to do:

- remove hardcoded Windows paths
- add config system
- add dependency file
- add unit tests
- add structured logging
- add error handling
- reduce oversized modules
- define current/production versions
- add API
- add UI
- add CI
- add deployment packaging

---

## 6. Immediate Next Step

### Right now

Wait for the currently running:

```powershell
python evaluation_suite_v3.py
```

When it finishes, save or paste these sections:

- CATEGORY RESULTS
- CORE METRICS
- TARGET STATUS
- FAILURE ANALYSIS

Do not make more broad architecture changes before reading that result.

The newest evaluation becomes the baseline.

---

## 7. What To Do After the Current V3 Run

### If all targets pass

If all of these pass:

- Semantic >= 95%
- Answer type >= 95%
- Support state >= 95%
- False-premise rejection >= 95%
- Supported acceptance >= 95%

Then:

1. freeze the working behavior
2. create a regression snapshot
3. fix remaining category-specific quality issues
4. add unit tests
5. begin production cleanup
6. make paths portable
7. create `requirements.txt`
8. create config management
9. add API layer
10. add UI/demo
11. benchmark against external baselines
12. collect real-user tests

### If semantic accuracy still fails

Inspect only the failed cases.

Do not rewrite large parts of the system.

For each failed case, determine whether the failure is:

- wrong intent
- bad subject extraction
- bad canonical question
- bad retrieval
- bad premise validation
- bad synthesizer
- missing required keyword
- latency failure

Then patch the smallest responsible component.

### If false-premise rejection still fails

Check:

1. `extract_asserted_relation()`
2. relation marker coverage
3. premise retrieval
4. `validate_asserted_relation()`
5. early return in `answer_question()`

Add only the missing relation form.

### If Roman structure remains the main failure

Inspect retrieval for the five Roman military questions.

Goal:

ensure context containing:

- legion
- cohort
- century / centuries
- units

is ranked above irrelevant Roman-history chunks.

Likely fixes:

- stronger query weighting
- explicit structure evidence boost
- required-term-aware reranking
- cohort keyword boost
- answer sentence selection requiring structure terms

---

## 8. Recommended Development Order

### Phase 1 — Evaluation stability

Goal:

consistently pass V3 targets over repeated runs.

Tasks:

- fix remaining semantic failures
- fix Roman structure retrieval
- remove planner misclassification
- rerun V3 multiple times
- make results stable, not lucky

Definition of done:

all target metrics >= 95% in repeated runs.

### Phase 2 — Regression safety

Goal:

make future changes safe.

Tasks:

- add focused unit tests
- add regression cases for every bug fixed
- add false-premise pattern tests
- add planner tests
- add retrieval ranking tests

Definition of done:

any previously fixed bug causes a test failure if reintroduced.

### Phase 3 — Engineering cleanup

Goal:

make the project portable and maintainable.

Tasks:

- create `config.py` or YAML config
- remove absolute Windows paths
- create `requirements.txt`
- pin dependency versions
- add logging
- add exceptions and graceful error messages
- identify current production files
- archive old versions

### Phase 4 — Product layer

Goal:

make the system usable outside the developer terminal.

Tasks:

- FastAPI API
- request schema
- response schema
- health endpoint
- web UI
- document ingestion
- authentication
- usage limits
- deployment container

### Phase 5 — Commercial proof

Goal:

make the project valuable to buyers.

Tasks:

- independent benchmark suite
- real customer use cases
- proprietary or specialized datasets
- case studies
- measurable accuracy advantage
- latency/cost comparison
- users
- revenue or pilots
- defensible IP / know-how

---

## 9. Commercial Goal Tracking

Long-term target:

potential multimillion-dollar commercial value.

Important:

A project does not become worth millions because the code reaches 100% on one internal test suite.

Commercial value comes from a combination of:

- technical quality
- defensibility
- reliable benchmarks
- production readiness
- portability
- real-world usefulness
- users
- revenue
- strategic fit for buyers

Current technical progress is strong enough to continue building, but valuation should not be treated as a fixed number yet.

The project should first become:

1. technically reliable
2. reproducible
3. deployable
4. independently benchmarked
5. useful to actual users
6. commercially validated

---

## 10. Rules For Future Changes

When modifying the system:

1. Do not patch blindly.
2. Reproduce the failure first.
3. Identify the responsible layer.
4. Make the smallest fix possible.
5. Run a targeted test.
6. Run regression tests.
7. Run V3.
8. Record the new metrics.
9. Update this README.
10. Do not delete the last known-good version until the new one passes.

---

## 11. README Update Procedure

After every meaningful change, update:

### Current baseline

Record:

- date
- commit/version
- evaluation suite
- semantic accuracy
- answer-type accuracy
- support-state accuracy
- content accuracy
- false-premise rejection
- supported acceptance
- latency
- failed cases

### Change log

Add:

- what file changed
- what bug was fixed
- why it was changed
- targeted test result
- full regression result

### Next action

Always write one clear next step.

Example:

`Next: inspect retrieval context for structure_006, structure_008, structure_013, structure_014, and structure_015.`

---

## 12. Current Change Log

### False-premise asserted-relation patch

Changed:

`rag_chat_v2.py`

Added detection for:

- `What caused X to overthrow Y?`
- `Why did X divide Y?`
- `How did X divide Y?`
- explain/describe divide variants

Expanded `split` relation markers with:

- divide
- divided
- divides
- dividing

Targeted result:

all seven known false-premise test questions are now rejected correctly.

Status:

PASS in targeted testing.

### Query-planner improvements

Changed:

`query_planner_v1.py`

Improved:

- intent classification
- subject extraction
- effect normalization
- Roman decline queries
- Roman aftermath queries
- Roman structure queries
- French Revolution entity queries
- mitosis/meiosis comparison variants

Status:

substantial improvement verified in V3 category results.

---

## 13. Current Status

Current stage:

**late evaluation / early stabilization**

The system is no longer at the prototype-from-scratch stage.

It already has:

- a working local model
- a working RAG pipeline
- intent-specific reasoning
- retrieval
- premise validation
- extensive evaluation
- strong performance on many categories

But it is not yet production-ready.

The immediate mission is:

**make V3 consistently pass, then freeze behavior and begin engineering/product hardening.**

---

## 14. Next Action

Current next action:

1. allow the active V3 run to finish
2. capture the final metrics
3. compare them with the previous baseline
4. update this README
5. fix only the remaining failed categories
