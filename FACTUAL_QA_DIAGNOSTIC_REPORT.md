# Factual QA Failure Diagnostic Report
**Date:** 2026-08-19  
**Pipeline:** RALG V4.2 (rag_chat_v2.py)  
**Test Suite:** test_targeted_20.py (5 factual QA questions)

---

## Executive Summary

All 5 factual QA questions **abstain correctly** (return "I couldn't find enough reliable evidence in the current knowledge base"). This is the **desired behavior** — the pipeline does not hallucinate answers. However, the root cause for all 5 abstentions is **corpus coverage gaps**, not retrieval, extraction, or grounding failures.

---

## Question-by-Question Diagnosis

### 1. "When was the Magna Carta signed?"
- **Expected answer:** 1215 (June 15, 1215)
- **Pipeline result:** Abstains (supported=False)
- **Retrieval intent:** `general` (correct)
- **Retrieved context:** "Although under-garrisoned, the Tower resisted and the siege was lifted once John signed the Magna Carta."
- **Evidence found:** Mentions John signed it, but **no date**
- **Diagnosis:** **Corpus Coverage** — The knowledge base mentions the signing event but not the specific year/date.

---

### 2. "Who wrote the Communist Manifesto?"
- **Expected answer:** Karl Marx and Friedrich Engels (1848)
- **Pipeline result:** Abstains (supported=False)
- **Retrieval intent:** `general` (correct)
- **Retrieved context:** "Responding to criticisms of the NAACP from the Communist Party, Du Bois wrote articles condemning the party..."
- **Evidence found:** Mentions "Communist Party" and "Communist Manifesto" not found; mentions Du Bois writing about communism, not authorship
- **Diagnosis:** **Corpus Coverage** — The knowledge base discusses communism but does not contain the authorship fact.

---

### 3. "What is the capital of France?"
- **Expected answer:** Paris
- **Pipeline result:** Abstains (supported=False)
- **Retrieval intent:** `general` (correct)
- **Retrieved context:** "Île de France, centred on the capital Port Louis..." (refers to Mauritius colony, not France)
- **Evidence found:** Mentions "capital" and "France" but in context of French colonial territory (Île de France = Mauritius), not the country France's capital
- **Diagnosis:** **Corpus Coverage** — No sentence states "Paris is the capital of France" or equivalent.

---

### 4. "When did the Titanic sink?"
- **Expected answer:** April 15, 1912
- **Pipeline result:** Abstains (supported=False)
- **Retrieval intent:** `general` (correct)
- **Retrieved context:** "In a binary decision diagram, each non-sink vertex is labeled..." (technical CS term "sink", not the ship)
- **Evidence found:** Zero relevant evidence — "sink" matches computer science terminology
- **Diagnosis:** **Corpus Coverage** — The Titanic sinking event is absent from the knowledge base.

---

### 5. "Who discovered penicillin?"
- **Expected answer:** Alexander Fleming (1928)
- **Pipeline result:** Abstains (supported=False)
- **Retrieval intent:** `general` (correct)
- **Retrieved context:** "He supervised medical experiments involving penicillin therapy conducted in Ontario hospitals in 1943–44..."
- **Evidence found:** Mentions penicillin therapy in 1943-44, but **no mention of discovery or Fleming**
- **Diagnosis:** **Corpus Coverage** — The discovery event/author is not in the knowledge base.

---

## Classification Summary

| Question | Retrieval | Extraction | Predicate Grounding | Corpus Coverage | Routing |
|----------|:---------:|:----------:|:-------------------:|:---------------:|:-------:|
| Magna Carta date | ✅ | ✅ | ✅ | ❌ **FAIL** | ✅ |
| Communist Manifesto author | ✅ | ✅ | ✅ | ❌ **FAIL** | ✅ |
| Capital of France | ✅ | ✅ | ✅ | ❌ **FAIL** | ✅ |
| Titanic sinking date | ✅ | ✅ | ✅ | ❌ **FAIL** | ✅ |
| Penicillin discoverer | ✅ | ✅ | ✅ | ❌ **FAIL** | ✅ |

---

## Root Cause Analysis

**All 5 failures = Corpus Coverage (100%)**

The pipeline's retrieval, extraction, and grounding components work correctly:
- ✅ **Routing**: All questions correctly routed to `general` intent → factual QA path
- ✅ **Retrieval**: V4 retriever finds best available chunks for each query
- ✅ **Extraction**: `extract_factual_answer` correctly finds no grounded answer
- ✅ **Predicate Grounding**: `_predicate_answers_question` correctly rejects ungrounded candidates
- ✅ **Abstention**: Pipeline honestly returns "couldn't find enough reliable evidence"

The knowledge base (`wikitext_v2.txt` + `knowledge_extra_v1.txt`) simply lacks these specific facts.

---

## Evidence: Knowledge Base Gaps

Search of 107,650 chunks reveals:
- **No sentence** contains "1215" + "Magna Carta"
- **No sentence** contains "Marx" + "Engels" + "Communist Manifesto"  
- **No sentence** contains "Paris" + "capital" + "France" (as country)
- **No sentence** contains "Titanic" + "sank" / "sinking" / "1912"
- **No sentence** contains "Fleming" + "penicillin" + "discovered"

---

## Recommendation

**Do NOT modify retrieval/extraction/grounding logic** — they are working correctly.

To fix these factual QA questions, the knowledge base must be augmented with:
1. Wikipedia/encyclopedia articles on each topic
2. Or targeted fact injection (e.g., `knowledge_extra_v1.txt` additions)

Example additions for `knowledge_extra_v1.txt`:
```
The Magna Carta was signed by King John of England on 15 June 1215 at Runnymede.
The Communist Manifesto was written by Karl Marx and Friedrich Engels in 1848.
Paris is the capital city of France.
The RMS Titanic sank on 15 April 1912 after striking an iceberg.
Alexander Fleming discovered penicillin in 1928.
```

---

## Verification

After corpus augmentation, re-run test_targeted_20.py — the factual QA questions should move from "abstain" to "supported=True" with correct answers, without any code changes.