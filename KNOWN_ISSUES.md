# Known Issues & Findings Tracker

An honest list of what this learning project still does not do well, what was found and fixed while preparing it, and how each fix was checked.

- **Open** = still true today. **By design** = a deliberate limit of a learning baseline (the docs teach the upgrade). **Fixed** = changed in the repo.
- **Final verification pass (2026-11-01), all on the final code with `openai/gpt-oss-20b` and the tool agent on `openai/gpt-oss-120b` (Groq), local embeddings, LangSmith tracing off:** 46 of 46 tests pass; all 24 examples exit cleanly and print correct output (read, not just exit codes); the evals score 5/5; a clean install of `requirements.txt` into a brand-new virtual environment on Python 3.12.1 worked (about 5 minutes) and passed the quickstart check and all 46 tests there too; an end-to-end spot check of 8 further questions was correct (the store-opening checklist now lists all 6 steps).
- Things that were not tested are listed in section 4.

---

## 1. What is still open or limited

| ID | Status | Limit | Where | What a learner should know |
|---|---|---|---|---|
| L1 | By design | No prompt-injection detection, no PII scrubbing, no RBAC / metadata-filtered retrieval, no per-user identity, no per-user rate limiting. Authentication is one shared API key. | `app/security.py` | Doc 30 teaches these as exercises. A model that refuses an injection-style prompt produces HTTP 422 `model_refused`, but that is model behaviour, not a defence. |
| L2 | By design | Chat history and the response cache live in one process's memory: history is per `session_id` but unbounded, lost on restart and not shared between workers. | `app/memory.py`, `app/cache.py` | Docs 24 and 29 describe the Redis upgrade path. |
| L3 | By design | The LangGraph version is a parallel demo: the CLI and API use `run_router()`, not the graph. | `app/graph/` | Stated in the `graph.py` docstring and doc 33. Examples 23-28 run it. |
| L4 | By design | The router picks exactly one route per question, so a combined question loses half (for example "What does the SOP say and are there open incidents?" is answered by the tools route only). | `app/router.py` | Doc 23 explains the trade-off. |
| L5 | Open (upstream) | `SemanticChunker` comes from `langchain-experimental`, which prints a "being sunset" warning. | `app/rag.py` | Recursive chunking is the fallback (`ENABLE_SEMANTIC_CHUNKING=false`). Noted in doc 10. |
| L6 | Open | A model that fails most of the time cannot be rescued by the single retry. `gpt-oss-20b` failed multi-tool questions in 6 of 8 and then 8 of 8 runs, which is why the tool agent has its own model. After the retry a persistent provider failure returns HTTP 502. | `app/llm.py`, `app/config.py` | Doc 21 has the measurements. |
| L7 | Open | `retrieve_with_multi_query()` skips reranking for any retriever that has no `reranker` attribute. | `app/multi_query.py` | Both real callers pass the hybrid retriever, so the app is unaffected. |
| L8 | Open | Eval reports do not record `RERANK_MIN_SCORE`, the chunking settings or `TOOLS_LLM_MODEL`, so two runs that differ only in those look identical when compared. | `evals/evaluation_report.py` | Noted in doc 19. |
| L9 | Open | The eval set has 5 questions (`wc -l` shows 4: no trailing newline), and the judge uses the same model as the generator, which can inflate scores. | `evals/` | Doc 19 says so and shows how to build a bigger set. |
| L10 | Open | The router tests are end-to-end (`tests/test_router.py` needs a key and can vary between runs); the other 43 tests use fakes. | `tests/` | Doc 28 explains the split. |
| L11 | Open | `gpt-oss` models write typographic characters (non-breaking hyphens U+2011), so exact-string checks on answers can fail. | tests, evals | `test_router.py` normalises them. |
| L12 | Open | The per-model free-tier limits are tight: on the key used here `gpt-oss-20b` allowed 8,000 tokens/minute and 200,000 tokens/day. A first RAG question makes 3 LLM calls, a follow-up 4. Running the whole suite, every example and the evals repeatedly in one day can exhaust it. | Groq account | The app answers "The AI service is busy right now" (HTTP 429). See the root README. |
| L13 | Open | Model names are hosted-catalogue facts that change. `llama-3.3-70b-versatile` disappeared from the key used here. | `.env.example` | HTTP 503 `model_unavailable` tells you; the README shows how to list available models. |
| L14 | Open | Model quality varies by model. With `qwen/qwen3.8-27b` as the router, "What does P1 mean?" went to the general route and was answered from the model's own knowledge. Follow-up questions ("What about part-time employees?") were sometimes answered "I don't know" in early runs. | router / RAG prompts | Not re-tested systematically on the final code. |

## 2. Fixed during the preparation (with how it was checked)

### Correctness bugs in the app

| ID | Problem | Fix | Checked by |
|---|---|---|---|
| F1 | `Chroma.from_documents()` without IDs appended a full copy of the corpus on every start, test run and debug call (460 stored entries for 22 distinct texts) | Stable content-based chunk IDs (SHA-256 of source + text) so Chroma upserts (`app/vectorstore.py`) | 3 repeated builds kept the count constant |
| F2 | The semantic chunker split a numbered list in half (it treats "6." as the end of a sentence), so the store-opening checklist answer reported step 6 as "not specified" | Sentence regex that skips bare list numbers plus `min_chunk_size=300` (`app/rag.py`); the checklist is now one chunk (8 chunks became 6) | Offline chunk inspection; relevant chunk found for 22 of 22 test questions |
| F3 | `/index/rebuild` deleted the index folder under an open handle ("attempt to write a readonly database") and left the running app on the old index | Deletes the Chroma collection in place, clears the container and response caches and rebuilds the container: no restart | Live: rebuild then chat worked; entries equal the manifest count |
| F4 | Index fingerprint ignored chunking and embedding changes; `rebuild_index()` used different chunking from the retriever, mixing strategies; the manifest ignored `VECTORSTORE_DIR` | Fingerprint manifest next to the index folder; shared `chunk_documents()`; a missing index folder triggers a rebuild (`app/indexing.py`) | Unit tests + live (8 entries = `chunk_count`) |
| F5 | The tool agent failed most multi-tool questions on `gpt-oss-20b` | Separate `TOOLS_LLM_MODEL` (default `openai/gpt-oss-120b`) for the tool agent | 8 of 8 runs passed |
| F6 | Any model refusal or parse failure became a generic HTTP 500; no retry; the exception classes were unused | Typed errors with code, message and HTTP status; one retry on transient failures; `/chat` maps codes to 422/429/502/503/500 (`app/exceptions.py`, `app/llm.py`, `app/router.py`, `app/api.py`) | Unit tests; live injection prompt returned 422 |
| F7 | The cache key ignored history (a follow-up could get another conversation's answer), tool answers were cached, a hit skipped memory, a hit reported the first run's latency | Only a conversation's first question is cached or served from cache; only `general`/`rag`; tools never; a hit records the turn and has its own latency and `request_id` | Unit tests; live hit took 0.35 ms vs 2,028 ms |
| F8 | Chat memory was one global history; the general and tools routes never saw it | Per-`session_id` history; all four routes get the last 6 messages | Unit tests; live follow-ups on the tools and general routes |
| F9 | API key compared with plain `!=`; the placeholder key was accepted anywhere | Constant-time compare; the app refuses to start with the placeholder key unless `APP_ENV=local` | Unit tests |
| F10 | `retrieve_with_multi_query()` created a new reranker on every question (about 2 s and about 36 Hugging Face requests) and ignored `ENABLE_RERANKING`; its LLM chain was rebuilt every call | One reranker built at start-up and reused; the chain is cached | Model loads once across 3 questions; retrieval fell from about 6.4 s to under 1 s |
| F11 | No relevance cut-off after reranking, so an irrelevant second chunk always reached the LLM | `RERANK_MIN_SCORE` (default -9.0, `none` disables); the best chunk is always kept | Measured on 23 questions; evals still 5/5 |
| F12 | The first RAG question made a useless rewrite call; the embedding model was loaded twice at start-up | Rewrite skipped when there is no history; `get_embeddings()` cached | `rewrite_ms` about 0.01; one embedding construction |
| F13 | `/debug/retrieval` re-chunked, re-embedded and wrote to the index on every call | Reuses the container's retriever and rewriter | 0.7 s, index entry count unchanged |
| F14 | LangGraph: the `rag` node was a placeholder (answer `None`), `tools_node` returned a stringified dict, nodes built chains at import (needed an API key), timings accumulated across turns | Real three-step RAG subgraph, `tools_node` reads the last message, lazy chains, per-turn timings and debug, errors route to the error node | Examples 23-28 print real answers; graph builds with no key |
| F15 | The general chat prompt claimed capabilities the app does not have (scheduling, sales reports) | The prompt states what the assistant can really do | Live: "What can you help me with?" |

### Examples, tests, packaging and docs

| ID | Problem | Fix |
|---|---|---|
| F16 | `examples/06` crashed (`rag_prompt` needs `rewritten_question`); `examples/11` tools follow-up got no history; `examples/17` searched for a SKU that is not in the indexed text; `examples/23` had two questions commented out; `examples/24` always raised `NameError`; `examples/25` made an unused call | Each fixed; all 24 examples exited cleanly in the last sweep (see section 4 for its caveats) |
| F17 | `pytest` failed on a fresh clone: `test_rag` shared the app's index folder, which the first router call then removed; the tools test failed on non-breaking hyphens | Temporary index for the retrieval test; hyphen normalisation in the router test |
| F18 | Test suite: 9 tests, none for errors, cache, sessions, security, index rules, reranker, graph | 37 new tests (46 total); none of the new ones needs a key or a model |
| F19 | CLI logs: about 150 library lines per question buried the app's own; the first question paid the whole start-up cost | Noisy loggers quieted (the `groq` retry lines stay visible); the CLI builds the app at start and shows `(served from cache)` |
| F20 | `requirements.txt` unpinned, missing `langgraph`, duplicate entry; default model `llama-3.3-70b-versatile` not available; root README unclosed fence and pasted unrelated doc; hard-coded personal paths in `RUN.md` | Pinned to tested versions (+ `langchain-classic`); default `openai/gpt-oss-20b`; README rewritten; paths removed |
| F21 | Docs described code that did not exist (security functions, JSON logging, `EnsembleRetriever` weights, `AgentExecutor`, per-session claims, restart after rebuild, ...) and had stale numbering | All 37 docs and both READMEs audited against the code; embedded code listings checked; doc 37 checklist re-scored (Level 1 12/12, Level 2 24/28, Level 3 0/18) |

## 3. Environment and model notes

- Models visible to the key used here included `openai/gpt-oss-20b`, `openai/gpt-oss-120b`, `openai/gpt-oss-safeguard-20b` and `qwen/qwen3.8-27b`. `gpt-oss-safeguard-20b` is a safety-classification model with only 2,000 tokens/minute; it is not a good default.
- Only the LLM is hosted. The embedding model (`all-MiniLM-L6-v2`) and the reranker (`ms-marco-MiniLM-L-6-v2`) run locally. Their Hugging Face repos redirect, so each model load follows 307 redirects and probes optional files (404s are normal). `HF_HUB_OFFLINE=1` removes this once the models are cached.
- The first start after the manifest format changed rebuilds the index once.
- `TOOLS_LLM_MODEL` set to an **empty value** in `.env` means "use `LLM_MODEL`", which puts the tool agent back on `gpt-oss-20b` and brings back the multi-tool failures. Leave the line out or give it a model name.

## 4. Unverified claims and untested paths

- Everything was tested on one machine (macOS) with one provider (Groq). Python 3.10.13 (development) and 3.12.1 (clean install) were both used; Linux, Windows and other Python versions are untested.
- The verification pass ran each example once. LLM output varies from run to run, so a specific answer can differ on your machine; the checks confirm the behaviour, not the exact wording.
- Doc code snippets were checked for import paths and, for listings that claim to be a repo file, against the file. Snippets were not executed.
- Claims written from general knowledge and never tested: `create_agent` is built on LangGraph; its default `recursion_limit` is 25.
- Timing figures quoted in the docs (retrieval 0.6-0.9 s, end to end 1.5-2.5 s) come from earlier live runs and were not re-measured after the chunking change.
