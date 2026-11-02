# App Lifecycle Initialization

## What

Application lifecycle initialization means creating expensive dependencies once when the app starts, then reusing them for every request.

## Why

RAG chains, retrievers, vector stores, tools, and agents can be expensive to create. Rebuilding them for every request increases latency and cost.

## When

Use this pattern when building APIs, services, or production assistants.

## Where

Implemented in:

- `app/container.py`
- `app/router.py`

## Example

```python
container = get_container()
result = container.rag_chain.invoke({"question": question})

# Structured Logging

## What

Structured logging means writing logs in a predictable format that includes useful fields such as request ID, route, latency, and errors.

## Why

Production AI systems are hard to debug without visibility. Logs help answer:

- What question was asked?
- Which route was selected?
- How long did the request take?
- Did the LLM fail?
- Did the retriever fail?
- Did the tool fail?

## When

Use structured logging in every API or service-based AI application.

## Where

Implemented in:

- `app/logging_config.py`
- `app/router.py`
- `app/api.py`
- `app/main.py`

## Example

```python
logger.info(
    "request_completed request_id=%s route=%s latency_ms=%s",
    request_id,
    route,
    latency_ms,
)

# API Request and Response Schemas

## What

API schemas define the shape of incoming requests and outgoing responses.

## Why

Production APIs need predictable contracts so frontend apps, services, and tests know what to expect.

## When

Use schemas for every public API endpoint.

## Where

Implemented in:

- `app/schemas.py`
- `app/api.py`

## Example

```python
class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    request_id: str
    route: str
    answer: str


# Central Service Layer

## What

A service layer is a single interface that application entry points use to access business logic.

## Why

Without a service layer, API, CLI, tests, and future workflows may each call router or chain logic differently.

## When

Use it when an application has more than one entry point.

## Where

Implemented in:

- `app/services.py`
- `app/api.py`
- `app/main.py`

## Example

```python
result = assistant_service.ask(question)

# Custom Exceptions and Safe Error Handling

## What

Custom exceptions define application-specific error categories. Safe error handling means users receive helpful messages while internal error details remain in logs.

## Why

Production systems should not expose raw stack traces, API errors, file paths, keys, or implementation details to users.

## When

Use custom exceptions and safe fallbacks in any public API or assistant.

## Where

Implemented in:

- `app/exceptions.py`
- `app/router.py`
- `app/tools.py`

## Example

```python
try:
    result = chain.invoke(...)
except Exception:
    logger.exception("request failed")
    return safe_error_response

    # RAG Evaluation Dataset

## What

A RAG evaluation dataset is a set of questions with expected answers and expected sources.

## Why

A RAG system can run without errors but still answer incorrectly. Evaluation helps measure whether retrieval and generation are working.

## When

Use evaluation whenever you change chunking, prompts, embedding models, retriever settings, vector stores, or LLM models.

## Where

Implemented in:

- `evals/rag_questions.jsonl`
- `evals/run_rag_eval.py`

## Example

```json
{
  "question": "How many vacation days do full-time store employees receive?",
  "expected_answer": "18 paid vacation days",
  "expected_source": "hr_policy.txt"
}

# LangSmith Trace Metadata

## What

Trace metadata adds tags and contextual information to LangSmith traces.

## Why

Production AI systems generate many traces. Tags and metadata help filter and debug requests by route, environment, version, and request ID.

## When

Use trace metadata when running any LangChain app with observability enabled.

## Where

Implemented in:

- `app/tracing.py`
- `app/router.py`

## Example

```python
chain.invoke(
    {"question": question},
    config={
        "tags": ["retailops", "rag", "local"],
        "metadata": {
            "request_id": request_id,
            "route": "rag"
        }
    }
)

# Hybrid Search Baseline

## What

Hybrid search combines vector retrieval with keyword retrieval.

## Why

Vector search is good for semantic meaning, but it can miss exact terms such as SKUs, policy codes, dates, and incident priorities.

## When

Use hybrid search when your documents contain exact identifiers, codes, product IDs, dates, or domain-specific acronyms.

## Where

Implemented in:

- `app/hybrid_retriever.py`
- `app/vectorstore.py`
- `app/chains.py`
- `examples/15_hybrid_retrieval.py`

## Example

```python
retriever = get_hybrid_retriever(db, chunks)
docs = retriever.invoke("What does P1 mean?")

# Cross Encoder Reranking

## What

A Cross Encoder reranker is a model that receives a query and a document chunk together, then returns a relevance score.

## Why

Vector search finds candidate chunks quickly, but it may not order them perfectly. A Cross Encoder improves ranking quality by evaluating the query and document together.

## When

Use Cross Encoder reranking after initial retrieval, especially when answer quality depends on selecting the best few chunks.

## Where

Implemented in:

- `app/reranker.py`
- `app/hybrid_retriever.py`
- `app/vectorstore.py`

## Example

```python
pairs = [
    ("What does P1 mean?", "P1 means full store outage."),
    ("What does P1 mean?", "Store opening checklist.")
]

scores = model.predict(pairs)

# Retrieval Debug Metadata

## What

Retrieval debug metadata records which documents were retrieved, their sources, and reranking scores.

## Why

RAG failures often happen because the wrong context was retrieved, not because the LLM failed.

## When

Use retrieval metadata during development, evaluation, and production debugging.

## Where

Implemented in:

- `app/reranker.py`
- `app/chains.py`

## Example

```text
Source: it_support_kb.txt
Rerank Score: 8.72

# Response Caching

## What

Response caching stores previous answers for repeated questions.

## Why

LLM and retrieval calls are expensive. If the same question is asked repeatedly, caching can reduce latency and cost.

## When

Use caching for repeated, low-risk, read-only questions.

## Where

Implemented in:

- `app/cache.py`
- `app/services.py`

## Example

```python
cached = response_cache.get(question)

if cached:
    return cached

# Health Diagnostics Endpoint

## What

A health diagnostics endpoint reports whether the application and critical dependencies are available.

## Why

Production systems need health checks for deployment, monitoring, load balancers, and debugging.

## When

Use health endpoints in every API service.

## Where

Implemented in:

- `app/health.py`
- `app/api.py`
- `app/cache.py`

## Example

```http
GET /health

# Document Versioning and Vectorstore Rebuild Strategy

## What

Document versioning tracks which document set was used to build the vector index.

## Why

If documents change but the vector store is not rebuilt, the assistant may answer using stale information.

## When

Use document versioning whenever RAG documents are updated, replaced, or reprocessed.

## Where

Implemented in:

- `.env`
- `app/config.py`
- `app/indexing.py`
- `app/container.py`
- `app/health.py`
- `app/api.py`

## Example

```env
DOCUMENT_VERSION=2026-06-08-v1

# BM25 Retrieval

## What

BM25 is a keyword ranking algorithm used to find documents based on exact lexical matches.

## Why

Vector search is strong for semantic meaning, but weaker for exact identifiers such as SKUs, dates, incident IDs, and policy codes.

## When

Use BM25 when documents contain important exact terms like P1, POS, DENIM-4421, INC-1001, or October 31.

## Where

Implemented in:

- `app/bm25_retriever.py`
- `app/hybrid_retriever.py`
- `examples/17_bm25_retrieval.py`

## Example

```python
retriever = BM25Retriever(chunks)
results = retriever.invoke("What does P1 mean?")

# Semantic Chunking

## What

Semantic chunking splits documents based on meaning and topic shifts rather than only character count.

## Why

Retrieval quality depends heavily on chunk quality. If a chunk mixes unrelated topics or cuts a thought in half, retrieval and answer quality suffer.

## When

Use semantic chunking when documents contain multiple topics, sections, or paragraphs where meaning changes naturally.

## Where

Implemented in:

- `app/rag.py`
- `app/parent_child.py`
- `examples/19_semantic_chunking.py`

## Example

Character chunking may split by size:

```text
Vacation policy ... P1 means full

# Multi-Query Retrieval

## What

Multi-query retrieval generates multiple search queries from one user question and retrieves documents for each query.

## Why

Users may phrase questions differently from how documents are written. Multi-query retrieval improves recall by searching multiple phrasings.

## When

Use multi-query retrieval when retrieval misses relevant documents due to wording mismatch, vague questions, or domain terminology differences.

## Where

Implemented in:

- `app/multi_query.py`
- `app/chains.py`
- `examples/21_multi_query_retrieval.py`

## Example

Original question:

```text
How much PTO do employees get?

# Configurable Multi-Query Retrieval

## What

Configurable multi-query retrieval allows the application to enable or disable multi-query retrieval using an environment variable.

## Why

Multi-query retrieval can improve recall, but it adds extra LLM and retrieval calls. Production systems should be able to control this tradeoff.

## When

Enable it for vague, high-value, or difficult questions. Disable it when latency and cost are more important.

## Where

Implemented in:

- `.env`
- `app/config.py`
- `app/chains.py`

## Example

```env
ENABLE_MULTI_QUERY=true

import json
from pathlib import Path

from app.container import get_container
from evals.evaluation_report import (
    save_evaluation_report
)
from evals.judge import judge_answer

EVAL_FILE = Path("evals/rag_questions.jsonl")


def normalize(text: str) -> str:
    return text.lower().strip()


def run_eval():
    container = get_container()
    total = 0
    passed = 0
    details = []
    with open(EVAL_FILE, "r") as file:
        for line in file:
            total += 1
            item = json.loads(line)

            question = item["question"]
            expected_answer = normalize(item["expected_answer"])
            expected_source = item["expected_source"]

            result = container.rag_chain.invoke({
                "question": question
            })

            answer = normalize(result.answer)
            sources = " ".join(result.sources)

            answer_match = expected_answer in answer
            source_match = expected_source in sources

            success = answer_match and source_match

            if success:
                passed += 1

            print("\nQuestion:", question)
            print("Expected Answer:", item["expected_answer"])
            print("Actual Answer:", result.answer)
            print("Expected Source:", expected_source)
            print("Actual Sources:", result.sources)
            print("Passed:", success)
            
            details.append(
                {
                    "question": question,
                    "success": success,
                    "expected_answer": item["expected_answer"],
                    "actual_answer": result.answer,
                    "expected_source": expected_source,
                    "actual_sources": result.sources,
                }
            )

    print("\nRAG Eval Summary")
    print("Passed:", passed)
    print("Total:", total)
    print("Score:", f"{passed}/{total}")
    report_file = save_evaluation_report(
    total=total,
    passed=passed,
    details=details,
    )
    print(
    "\nSaved report:",
    report_file
    )
    

if __name__ == "__main__":
    run_eval()

# Retrieval and Answer Quality Metrics

## What

Evaluation metrics quantify RAG quality across source retrieval, answer correctness, groundedness, and completeness.

## Why

A RAG system may produce fluent answers while retrieving the wrong source. Metrics separate retrieval quality from generation quality.

## When

Use these metrics whenever changing prompts, chunking, retrievers, embeddings, rerankers, or models.

## Where

Implemented in:

- `evals/run_rag_eval.py`
- `evals/evaluation_report.py`

## Metrics

- `source_accuracy`: expected source was retrieved
- `judge_correct_rate`: answer was correct
- `judge_grounded_rate`: answer was grounded
- `judge_complete_rate`: answer was complete
- `pass_rate`: all required checks passed

## Pros

- Separates retrieval failures from LLM failures
- Helps tune RAG systematically
- Supports release decisions

## Cons

- Metrics depend on evaluation dataset quality
- LLM judge can be imperfect
- Small datasets can be misleading

# Retrieval Configuration Toggles

## What

Retrieval configuration toggles allow semantic chunking, reranking, and multi-query retrieval to be enabled or disabled through environment variables.

## Why

Production RAG systems require experimentation. Different retrieval strategies affect quality, latency, and cost.

## When

Use toggles when comparing retrieval approaches or running evaluation experiments.

## Where

Implemented in:

- `.env`
- `app/config.py`
- `app/chains.py`
- `app/hybrid_retriever.py`
- `app/debug.py`

## Example

```env
ENABLE_SEMANTIC_CHUNKING=true
ENABLE_RERANKING=true
ENABLE_MULTI_QUERY=false

# Evaluation Report Configuration Tracking

## What

Evaluation report configuration tracking stores retrieval settings inside every evaluation report.

## Why

A score without configuration is not useful. We need to know which chunking, reranking, multi-query, and retrieval settings produced the score.

## When

Use this whenever running retrieval or answer quality evaluations.

## Where

Implemented in:

- `evals/evaluation_report.py`

## Example

```json
"retrieval_config": {
  "enable_semantic_chunking": true,
  "enable_reranking": true,
  "enable_multi_query": true,
  "retrieval_k": 4
}

# Evaluation Report Comparison

## What

Evaluation report comparison reads previous evaluation reports and prints their metrics side by side.

## Why

RAG tuning requires comparing different retrieval configurations objectively.

## When

Use it after running multiple evaluation experiments.

## Where

Implemented in:

- `evals/compare_reports.py`
- `evals/results/`

## Example

```bash
python -m evals.compare_reports

# Production Baseline Completion Checklist

## Core LangChain

- [x] Prompt templates
- [x] LCEL chains
- [x] Chat model abstraction
- [x] Output parser
- [x] Structured output
- [x] Config-driven settings

## RAG

- [x] Document loading
- [x] Recursive chunking baseline
- [x] Semantic chunking option
- [x] Embeddings
- [x] Chroma vector store
- [x] Vector retrieval
- [x] BM25 retrieval
- [x] Hybrid retrieval
- [x] Cross-encoder reranking
- [x] Multi-query retrieval
- [x] History-aware question rewriting
- [x] Source attribution
- [x] Retrieval debug mode

## Tools and Agents

- [x] CSV tools
- [x] JSON tools
- [x] Tool agent
- [x] Router chain
- [x] Safe tool string responses

## API and App Architecture

- [x] FastAPI service
- [x] Central service layer
- [x] App container
- [x] Startup initialization
- [x] Health endpoint
- [x] API key protection
- [x] Request/response schemas

## Observability

- [x] Structured logging
- [x] Request IDs
- [x] Stage-level timing
- [x] Retrieval logs
- [x] LangSmith trace metadata

## Evaluation

- [x] Golden dataset
- [x] Deterministic checks
- [x] LLM-as-judge evaluation
- [x] Metrics
- [x] Evaluation reports
- [x] Report comparison
- [x] CSV export

## Production Limitations Still Remaining

- [ ] Persistent memory
- [ ] Redis/shared cache
- [ ] OAuth/SSO
- [ ] Role-based document access
- [ ] Metadata filtering
- [ ] Incremental indexing
- [ ] Deployment config
- [ ] Load testing
- [ ] Human-in-the-loop workflow
- [ ] LangGraph orchestration