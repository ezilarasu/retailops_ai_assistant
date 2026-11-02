# 36 - Caching

# Learning Objectives

After completing this document, you should understand:

* What Caching is
* Why Caching exists
* Response Caching
* Retrieval Caching
* Embedding Caching
* Cache Keys
* TTL (Time To Live)
* Cache Invalidation
* Memory vs Cache
* Redis Caching
* Production Best Practices
* RetailOps Implementation

---

# 1. What is Caching?

## Definition

Caching stores previously computed results so they can be reused instead of recomputed.

---

Without cache:

```text id="cache1"
Question
 ↓
Retriever
 ↓
Reranker
 ↓
LLM
 ↓
Answer
```

---

Every request repeats all work.

---

With cache:

```text id="cache2"
Question
 ↓
Cache
 ↓
Answer
```

---

Much faster.

---

# 2. Why Does Caching Exist?

AI systems are expensive.

---

Every request may involve:

```text id="cache3"
Retrieval
Reranking
LLM Calls
```

---

Question:

```text id="cache4"
What does P1 mean?
```

---

Asked:

```text id="cache5"
1000 times
```

---

Without caching:

```text id="cache6"
1000 LLM Calls
```

---

Wasteful.

---

# With Caching

```text id="cache7"
1 LLM Call
999 Cache Hits
```

---

Much cheaper.

---

# 3. Response Caching

Most common type.

---

Question:

```text id="cache8"
What does P1 mean?
```

---

Response:

```text id="cache9"
P1 means full store outage.
```

---

Stored in cache.

---

Next time:

```text id="cache10"
Return Cached Response
```

---

No LLM call required.

---

# RetailOps

Current:

```text id="cache11"
Response Cache
```

---

Implemented in:

```text id="cache12"
app/cache.py
```

---

# 4. Cache Flow

```text id="cache13"
Question
 ↓
Cache Check

Hit?
 ├── Yes → Return
 └── No
      ↓
      LLM
      ↓
      Store Result
```

---

# 5. Cache Hit

Question:

```text id="cache14"
What does P1 mean?
```

---

Already cached.

---

Result:

```text id="cache15"
cache_hit=True
```

---

No retrieval.

No generation.

---

# Benefit

```text id="cache16"
Fast
Cheap
```

---

# 6. Cache Miss

Question:

```text id="cache17"
New Question
```

---

No cache entry.

---

System performs:

```text id="cache18"
Retrieval
Reranking
Generation
```

---

Then stores result.

---

# 7. TTL (Time To Live)

## Definition

How long cache entries remain valid.

---

Example:

```text id="cache19"
5 minutes
```

---

After:

```text id="cache20"
Expiration
```

---

Entry removed.

---

RetailOps:

```text id="cache21"
TTL Cache
```

---

# Why?

Prevent:

```text id="cache22"
Stale Data
```

---

# 8. Cache Keys

Question:

```text id="cache23"
What does P1 mean?
```

---

Cache needs a key.

---

Example:

```python id="cache24"
hash(question)
```

---

Stored:

```text id="cache25"
key
↓
response
```

---

# Why Hash?

Efficient lookup.

---

# 9. Retrieval Caching

Different from response caching.

---

Cache:

```text id="cache26"
Retrieved Documents
```

---

Instead of:

```text id="cache27"
Final Answer
```

---

Flow:

```text id="cache28"
Question
 ↓
Cache
 ↓
Documents
```

---

Useful when:

```text id="cache29"
LLM Changes
```

but retrieval stays the same.

---

# 10. Embedding Caching

Question:

```text id="cache30"
What does P1 mean?
```

---

Embedding:

```text id="cache31"
Vector Q
```

---

Cache:

```text id="cache32"
Vector Q
```

---

Avoid recomputing embeddings.

---

Useful for:

```text id="cache33"
Large Volumes
```

---

# 11. Cache Invalidation

One of the hardest problems.

---

Question:

```text id="cache34"
Document changed.
```

---

Old answer:

```text id="cache35"
Still Cached
```

---

Problem:

```text id="cache36"
Stale Response
```

---

Need:

```text id="cache37"
Invalidate Cache
```

---

# RetailOps Strategy

Document Versioning.

---

When:

```text id="cache38"
DOCUMENT_VERSION
```

changes.

---

Rebuild.

---

# 12. Memory vs Cache

Very common confusion.

---

# Memory

Stores:

```text id="cache39"
Conversation History
```

---

Purpose:

```text id="cache40"
Context
```

---

# Cache

Stores:

```text id="cache41"
Computed Results
```

---

Purpose:

```text id="cache42"
Performance
```

---

# Difference

Memory:

```text id="cache43"
Conversation
```

---

Cache:

```text id="cache44"
Optimization
```

---

# 13. Local Cache vs Redis

## Local Cache

RetailOps current.

---

Pros:

```text id="cache45"
Simple
```

---

Cons:

```text id="cache46"
Lost On Restart
```

---

# Redis

Enterprise option.

---

Pros:

```text id="cache47"
Shared
Persistent
Scalable
```

---

Cons:

```text id="cache48"
Extra Infrastructure
```

---

# 14. RetailOps Cache

Current:

```python id="cache49"
SimpleTTLCache
```

---

Features:

```text id="cache50"
TTL
Response Cache
Cache Hit Tracking
```

---

Purpose:

```text id="cache51"
Reduce Cost
```

---

# 15. Why Caching Matters in Production

Without cache:

```text id="cache52"
Higher Cost
Higher Latency
```

---

With cache:

```text id="cache53"
Lower Cost
Lower Latency
```

---

Especially for:

```text id="cache54"
Frequently Asked Questions
```

---

# 16. Production Best Practices

## Cache Responses

Good default.

---

## Add TTL

Avoid stale answers.

---

## Track Cache Hit Rate

Metric:

```text id="cache55"
Hits / Requests
```

---

## Invalidate on Document Updates

Critical.

---

## Move to Redis

For production scale.

---

# 17. Common Mistakes

## Mistake 1

No expiration.

---

## Mistake 2

Caching dynamic data.

---

Example:

```text id="cache56"
Inventory Levels
```

---

Should not be cached long.

---

## Mistake 3

Ignoring document updates.

---

## Mistake 4

Confusing cache and memory.

---

## Mistake 5

No cache metrics.

---

# 18. Interview Questions

### What is caching?

Storing previously computed results for reuse.

---

### Why use caching in AI systems?

Reduce cost and latency.

---

### What is a cache hit?

Request served from cache.

---

### What is TTL?

Time To Live.

---

### Memory vs Cache?

Memory:

```text id="cache57"
Conversation
```

Cache:

```text id="cache58"
Performance
```

---

### Why isn't RetailOps cache enterprise-grade yet?

Because it is local and not shared.

---

# Summary

Caching is one of the highest ROI production optimizations.

RetailOps uses:

```text id="cache59"
TTL Response Cache
```

to reduce:

```text id="cache60"
Latency
Cost
Repeated Computation
```

while future enterprise upgrades may introduce:

```text id="cache61"
Redis
Distributed Caching
Cache Metrics
```

for large-scale deployments.

The next document:

```text id="cache62"
37_security.md
```

covers authentication, authorization, API protection, metadata filtering, and enterprise AI security patterns.
