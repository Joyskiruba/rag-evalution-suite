# RAG Evaluation Suite

Evaluates a small RAG system against a corpus of 8 internal-policy documents, scoring
**retrieval quality** and **generation quality** separately, since they fail differently.

## Structure
```
corpus/              8 markdown policy docs (40 chunks after splitting by heading)
chunker.py           loads + chunks the corpus
retrieval.py         TF-IDF retriever
generation.py        extractive baseline generator + optional real-LLM generator
qa_set.json          41 questions: 38 answerable + 3 deliberately unanswerable
evaluate.py          runs retrieval + generation eval, writes results/
results/
  results_table.csv  per-question results
  summary.json       aggregate metrics
  analysis.md         written interpretation
```

## Run it
```bash
pip install -r requirements.txt
python3 evaluate.py
```

## Swapping in a real LLM
`generation.py` ships an `llm_generate()` function that calls OpenAI's API.
Set `OPENAI_API_KEY` and change the two `extractive_generate(...)` calls in
`evaluate.py` to `llm_generate(...)` to see how a real model changes the
generation-quality numbers (retrieval numbers won't change — that's the point
of scoring them separately).

## Why TF-IDF instead of embeddings
This environment couldn't reach a model-hosting API to download embedding
weights, so retrieval uses TF-IDF + cosine similarity — fully local, and
transparent enough to explain exactly why a chunk matched in a review.
`retrieval.py` is a single small class; swapping in SBERT or OpenAI
embeddings only requires replacing `Retriever.fit`/`Retriever.query`.
