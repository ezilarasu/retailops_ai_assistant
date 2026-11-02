# CLAUDE.md — LangChain Learning App

## Project Purpose
This is a LangChain learning application built with RAG.
The goal is to teach every LangChain concept to developers through clear docs + working examples.
Target reader: knows Python, new to LangChain.

---

## Source Material (Do Not Delete)

The drafting phase is complete. Earlier raw notes and the intermediate rewrite pass are archived — read-only, never delete or overwrite:

| Folder | Notes |
|--------|-------|
| `docs/drafts/raw_notes/` | First-pass draft files that used to live loose in `docs/` root |
| `docs/drafts/granular_notes/` | Second-pass, per-concept draft files that used to live in `docs/langchain_learning/` |
| `docs/drafts/final_originals/` | The flat `docs/final/*.md` files before they were split into per-concept folders |

Everything of substance from these was folded into the current `docs/<NN>_<concept>/README.md` docs — check there first before assuming something's missing.

---

## Output Structure

**One doc folder per concept** under `docs/`, named with zero-padded numbers matching the concept's learning order. Nothing else belongs directly in `docs/` except `README.md` and `drafts/`:

```
docs/
├── README.md                          ← Master learning path index
├── 01_llms_and_chat_models/
│   ├── README.md                      ← the concept doc (13-section structure)
│   └── RUN.md                         ← how to run its matching examples/ script (only if one exists)
├── 02_langchain_overview/
│   └── README.md                      ← no RUN.md — no matching example script
├── ...
└── drafts/                            ← archived source material, see above
```

When adding a new concept doc: create `docs/<NN>_<slug>/README.md` following the 13-section structure below, and add `docs/<NN>_<slug>/RUN.md` only if there's a corresponding runnable file in `/examples/`. Update the table and links in `docs/README.md` to include it.

---

## Required Doc Structure (13 Sections — ALL docs must follow this exactly)

```
# [Concept Name]
> One-line summary

## 📌 What Is It?
## ❓ Why Does It Exist?
## ⏰ When Should You Use It?
## 🗂️ Types / Variants
## 🔀 When to Use Which Type
## ⚖️ Pros & Cons
## 💻 Basic Example
## 🔧 Real-World Example
## 🏭 Production Best Practices
## ⚠️ Common Mistakes to Avoid
## 🔗 How It Connects to Other Concepts
## 📚 Summary Table
## ➡️ Next Steps
```

Details for each section:

**What Is It?** — Plain English + analogy. No jargon without explanation.

**Why Does It Exist?** — What problem it solves. What you'd do without it.

**When Should You Use It?** — Bullet checklist: ✅ use when / ❌ don't use when.

**Types / Variants** — Table: `| Type | Description | Best For |`. If only 1 type exists, still include the section and note it.

**When to Use Which Type** — Decision paragraph or table between the types above.

**Pros & Cons** — Table: `| ✅ Pros | ❌ Cons |`

**Basic Example** — Minimal working code. Comments on every meaningful line.

**Real-World Example** — Production-realistic code, matches an actual file in `/examples/`.

**Production Best Practices** — Numbered list. Each item: **Bold title** — Why it matters + exactly how to do it. Must cover: error handling, cost/tokens, latency, security, observability, scalability.

**Common Mistakes to Avoid** — ⚠️ prefixed. Each: what goes wrong + what to do instead.

**How It Connects to Other Concepts** — Bullet list of relationships to other LangChain concepts.

**Summary Table** — 5-row table: What / Why / When / Types / Production gotcha.

**Next Steps** — Link to the `/examples/` file (and note the sibling `RUN.md` if one exists) + next doc (as `../NN_slug/README.md`) + official LangChain docs URL.

---

## Writing Rules

- Use **LangChain v0.3+ / LCEL syntax** (pipe operator `|`) — not legacy LLMChain
- Prefer `langchain_core`, `langchain_community` imports
- Every code block: runnable as-is, comments on key lines
- Tone: friendly + direct, like a senior dev to a junior dev
- Extract and preserve good content from existing source files — don't ignore it
- Improve clarity, fill gaps, add missing sections
- Use `python-dotenv` + `os.getenv()` for all API keys — never hardcode

---

## Concept Inventory Process

Before writing any doc:
1. Scan both source folders and list every unique concept
2. Deduplicate (e.g. `02_chat_models.md` and a chat models section in `01_llm_fundamentals.md` = 1 doc)
3. Assign a learning order number
4. Map source files → output file so content is not lost
5. Get approval before writing

---

## Learning Order Principle

Docs must build on each other. Rough order:
Core LLM concepts → Prompts → Chains → Memory → Parsers → Embeddings → Retrieval/RAG → Agents → Advanced patterns → Production/deployment

Each doc: reference the previous concept, tease the next one.

---

## Code Style

```python
# Always load keys from environment
import os
from dotenv import load_dotenv
load_dotenv()

# Always use LCEL pipe syntax for chains
chain = prompt | llm | output_parser

# Show async/streaming where relevant
async for chunk in chain.astream({"input": query}):
    print(chunk, end="", flush=True)
```

---

## What Claude Must NOT Do

- Do not overwrite or delete files in `docs/drafts/`
- Do not skip sections — all 13 are required even if brief
- Do not use deprecated `LLMChain` as the primary example (mention it as legacy only)
- Do not write vague best practices — be specific with code where possible
- Do not start writing until the concept inventory and learning order are approved
