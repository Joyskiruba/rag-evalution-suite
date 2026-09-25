"""
Evaluation harness.

Retrieval and generation are scored SEPARATELY, on purpose:

- Retrieval quality: for each answerable question, did the gold chunk
  come back in the top-k? (Recall@1, Recall@3, MRR). For unanswerable
  questions, did retrieval correctly return low-confidence matches
  (no chunk score above the abstain threshold)?

- Generation quality: given the CORRECT (gold) chunk handed to it directly
  -- i.e. assuming perfect retrieval -- did the generator produce the
  right answer? This isolates "can it read" from "can it find."
  We also report end-to-end (retrieved context, not gold) generation
  accuracy separately, since that's what a user actually experiences.

This split is what lets you say in a review: "retrieval finds the right
passage 91% of the time, but generation only gets it right 74% of the
time even when handed the right passage" -- two different bugs, two
different fixes.
"""
import json
import csv
import re
from chunker import load_chunks
from retrieval import Retriever
from generation import extractive_generate, ABSTAIN_MSG

ABSTAIN_THRESHOLD = 0.30
TOP_K = 3

STOPWORDS = {
    "the", "a", "an", "is", "are", "does", "do", "for", "of", "to", "in",
    "on", "and", "or", "what", "how", "many", "much", "under", "at", "must",
    "can", "with", "before", "after", "within", "under",
}


def keywords(text):
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOPWORDS}


def answer_correct(gold_answer, generated_text):
    if gold_answer is None:
        return None  # not applicable; handled via abstention check instead
    gold_kw = keywords(gold_answer)
    if not gold_kw:
        return gold_answer.lower() in generated_text.lower()
    gen_kw = keywords(generated_text)
    overlap = len(gold_kw & gen_kw) / len(gold_kw)
    return overlap >= 0.6


def find_chunk_by_id(chunks, chunk_id):
    for c in chunks:
        if c["chunk_id"] == chunk_id:
            return c
    return None


def main():
    chunks = load_chunks()
    retriever = Retriever(chunks)
    with open("qa_set.json") as f:
        qa_set = json.load(f)

    rows = []
    retrieval_hits_at_1, retrieval_hits_at_3, mrr_sum = 0, 0, 0.0
    n_answerable = 0
    unanswerable_correctly_flagged = 0
    n_unanswerable = 0

    gen_oracle_correct, gen_e2e_correct = 0, 0
    n_gen_scored = 0

    for qa in qa_set:
        question = qa["question"]
        gold_id = qa["gold_chunk_id"]
        gold_answer = qa["answer"]
        answerable = qa["answerable"]

        retrieved = retriever.query(question, k=TOP_K)
        retrieved_ids = [r["chunk_id"] for r in retrieved]
        top1 = retrieved[0]

        row = {
            "id": qa["id"],
            "question": question,
            "answerable": answerable,
            "gold_chunk_id": gold_id,
            "top1_chunk_id": top1["chunk_id"],
            "top1_score": round(top1["score"], 4),
            "retrieval_recall@1": None,
            "retrieval_recall@3": None,
            "retrieval_rank": None,
            "gen_oracle_correct": None,
            "gen_e2e_correct": None,
            "gen_e2e_answer": None,
        }

        if answerable:
            n_answerable += 1
            rank = (retrieved_ids.index(gold_id) + 1) if gold_id in retrieved_ids else None
            r_at_1 = int(gold_id == top1["chunk_id"])
            r_at_3 = int(gold_id in retrieved_ids)
            retrieval_hits_at_1 += r_at_1
            retrieval_hits_at_3 += r_at_3
            mrr_sum += (1.0 / rank) if rank else 0.0
            row["retrieval_recall@1"] = r_at_1
            row["retrieval_recall@3"] = r_at_3
            row["retrieval_rank"] = rank

            # --- Generation, ORACLE context (gold chunk handed directly) ---
            gold_chunk = find_chunk_by_id(chunks, gold_id)
            oracle_answer, oracle_abstained = extractive_generate(
                question, gold_chunk["text"], retrieval_score=1.0
            )
            oracle_correct = (not oracle_abstained) and answer_correct(gold_answer, oracle_answer)
            row["gen_oracle_correct"] = int(bool(oracle_correct))

            # --- Generation, END-TO-END (whatever retrieval actually returned) ---
            e2e_answer, e2e_abstained = extractive_generate(
                question, top1["text"], retrieval_score=top1["score"], score_threshold=ABSTAIN_THRESHOLD
            )
            e2e_correct = (not e2e_abstained) and answer_correct(gold_answer, e2e_answer)
            row["gen_e2e_correct"] = int(bool(e2e_correct))
            row["gen_e2e_answer"] = e2e_answer

            gen_oracle_correct += int(bool(oracle_correct))
            gen_e2e_correct += int(bool(e2e_correct))
            n_gen_scored += 1
        else:
            n_unanswerable += 1
            # Correct behavior: retrieval should NOT return a confident match,
            # and generation should abstain rather than invent an answer.
            e2e_answer, e2e_abstained = extractive_generate(
                question, top1["text"], retrieval_score=top1["score"], score_threshold=ABSTAIN_THRESHOLD
            )
            row["gen_e2e_answer"] = e2e_answer
            row["gen_e2e_correct"] = int(e2e_abstained)  # "correct" = abstained
            if e2e_abstained:
                unanswerable_correctly_flagged += 1

        rows.append(row)

    # ---- write results table ----
    fieldnames = list(rows[0].keys())
    with open("results/results_table.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # ---- summary ----
    summary = {
        "n_questions_total": len(qa_set),
        "n_answerable": n_answerable,
        "n_unanswerable": n_unanswerable,
        "retrieval_recall@1": round(retrieval_hits_at_1 / n_answerable, 3),
        "retrieval_recall@3": round(retrieval_hits_at_3 / n_answerable, 3),
        "retrieval_mrr": round(mrr_sum / n_answerable, 3),
        "generation_accuracy_oracle_context": round(gen_oracle_correct / n_gen_scored, 3),
        "generation_accuracy_end_to_end": round(gen_e2e_correct / n_gen_scored, 3),
        "unanswerable_correctly_abstained": f"{unanswerable_correctly_flagged}/{n_unanswerable}",
    }
    with open("results/summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
