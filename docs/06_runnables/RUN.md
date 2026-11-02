# How to Run These Examples

```bash
# from the repository root (data paths in the code are relative to it)
source .venv/bin/activate

python -m examples.12_runnable_lambda     # RunnableLambda: wraps a plain function in a chain
python -m examples.13_runnable_parallel   # RunnableParallel: runs multiple branches concurrently
python -m examples.14_runnable_branch     # RunnableBranch: conditional routing between chains
```

Requires: nothing beyond `pip install -r requirements.txt`. These three examples don't call the LLM, so no `GROQ_API_KEY` is needed. Run them from the repository root.
