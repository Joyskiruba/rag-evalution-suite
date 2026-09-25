# RAG Evaluation Suite — Results and Analysis

## Setup
- **Corpus:** 8 internal-policy documents (onboarding, remote work, expenses, incident response, API limits, billing, security, data retention), chunked into 40 sections by heading.
- **Retriever:** TF-IDF + cosine similarity, top-3.
- **Generator:** dependency-free extractive baseline (picks the sentence in the retrieved chunk with the most keyword overlap with the question); abstains below a similarity threshold.
- **Question set:** 41 questions — 38 answerable (one per chunk, minus two combined), 3 deliberately unanswerable (facts never mentioned in the corpus).

## Results

| Metric | Score |
|---|---|
| Retrieval Recall@1 | 0.974 (37/38) |
| Retrieval Recall@3 | 0.974 (37/38) |
| Retrieval MRR | 0.974 |
| Generation accuracy, oracle context (gold chunk handed directly) | 0.868 (33/38) |
| Generation accuracy, end-to-end (whatever retrieval actually returned) | 0.816 (31/38) |
| Unanswerable questions correctly abstained | 2/3 |

Full per-question breakdown: `results/results_table.csv`.

## Interpretation: retrieval and generation fail differently

**Retrieval is nearly perfect (97.4%) but not the bottleneck.** The one retrieval miss (q16, "How quickly must a SEV1 incident page the on-call engineer?") pulled the *Incident Commander* chunk instead of the *Severity Levels* chunk — both mention "SEV1," "SEV2," and "minutes," so the two chunks are lexically close enough to confuse a keyword-based retriever. This is a retrieval bug, and it is the *only* thing embeddings-based retrieval (SBERT/OpenAI) would likely fix that TF-IDF didn't.

**Generation loses ~11 more points even with the correct chunk handed to it** (86.8% oracle vs. 97.4% retrieval). That gap is *entirely* a generation problem, not a retrieval problem — swapping retrievers would not fix it. Two distinct causes, visible in `results_table.csv`:

1. **Wrong-sentence selection within a correct chunk.** For q02 ("How often does an onboarding buddy check in?"), the gold answer is in the sentence *"...informal check-ins twice a week..."*, but the extractive baseline picked the first sentence of the chunk instead, because it scored an equal or higher keyword overlap. Same failure mode on q04 (picked the training-deadline sentence instead of the consequence sentence).
2. **Morphological mismatch in scoring, not in the model.** For q24 and q30, the generated sentence *does* contain the right fact ("90-day deprecation notice", "7-day grace period") but was marked wrong because the answer-checker's keyword overlap treats "day" and "days" as different tokens. This is a lesson about the evaluator, not just the system: a naive exact/keyword match will under-count a generator that's actually right. A production eval would need lemmatization or an LLM-as-judge for the correctness check.

**Abstention on unanswerable questions is the weakest link (2/3).** At a low similarity threshold (0.08), the system never abstained — it answered all 3 unanswerable questions confidently by retrieving a topically-related but non-answering chunk (e.g., asked about an "Enterprise-tier discount," it retrieved the Enterprise Tier Limits chunk and generated an answer from it even though that chunk never mentions a discount). Raising the threshold to 0.30 catches 2 of 3, but the third unanswerable question (q41) scores *higher* (0.397) than five genuinely answerable low-confidence questions (as low as 0.263) — **there is no single similarity threshold that cleanly separates "topically related" from "actually answers the question."** This is the most defensible number in the whole suite to bring to a review: confidence-based abstention is a leaky heuristic, not a fix.

## What I would defend in a review

> "Retrieval works 97% of the time. The system's real weak points are (1) generation picking the wrong sentence within an otherwise-correct passage, and (2) an inability to reliably detect when the retrieved passage doesn't actually answer the question — similarity score alone isn't a good enough abstention signal, since an unanswerable question can score higher than a genuinely answerable one."

## Recommended next steps
1. Swap the extractive baseline for a real LLM call (`generation.py::llm_generate` is already wired up — just set `OPENAI_API_KEY`) and re-run to see how much of the generation gap a real model closes.
2. Replace keyword-overlap scoring in the answer-checker with lemmatization or an LLM-as-judge, since the current checker undercounts genuinely correct answers (see q24, q30).
3. Replace the pure similarity-threshold abstention with an explicit "does this passage answer this question, yes/no" check (a second, cheap LLM call) rather than trusting the retrieval score alone.
4. Fix the q16-style retrieval confusion by testing embedding-based retrieval on the small number of lexically-similar chunk pairs identified here.
