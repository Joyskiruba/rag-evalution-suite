"""
Generation component.

Two generators are provided:

1. extractive_generate() - a dependency-free baseline that picks the
   sentence in the retrieved chunk with the most keyword overlap with the
   question. No API key needed, runs anywhere. This is what the shipped
   eval numbers use.

2. llm_generate() - a real LLM call via the OpenAI API. Disabled unless
   OPENAI_API_KEY is set in the environment. Swap this in to see how much
   of the generation-quality gap the extractive baseline is responsible
   for versus retrieval.

Both take (question, context_text) and return (answer_text, abstained: bool).
"""
import os
import re

ABSTAIN_MSG = "I don't have enough information in the provided context to answer that."

STOPWORDS = {
    "the", "a", "an", "is", "are", "does", "do", "for", "of", "to", "in",
    "on", "and", "or", "what", "how", "many", "much", "under", "at", "must",
    "can", "with", "before", "after", "within",
}


def _keywords(text):
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOPWORDS}


def extractive_generate(question, context_text, retrieval_score=None, score_threshold=0.08):
    """Rule-based baseline: no LLM call, pure keyword overlap."""
    if retrieval_score is not None and retrieval_score < score_threshold:
        return ABSTAIN_MSG, True

    body = re.sub(r"^##\s+.+\n", "", context_text).strip()  # drop the markdown header line
    sentences = re.split(r"(?<=[.!?])\s+", body)
    q_kw = _keywords(question)
    best_sentence, best_overlap = None, -1
    for s in sentences:
        overlap = len(q_kw & _keywords(s))
        if overlap > best_overlap:
            best_overlap, best_sentence = overlap, s
    if best_sentence is None or best_overlap == 0:
        return ABSTAIN_MSG, True
    return best_sentence.strip(), False


def llm_generate(question, context_text, retrieval_score=None, score_threshold=0.08):
    """Real LLM generation. Requires OPENAI_API_KEY. Falls back to abstain-style
    message if the key is missing, so the harness never crashes without one."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "[llm_generate skipped: OPENAI_API_KEY not set]", True

    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    prompt = (
        "Answer the question using ONLY the context below. "
        "If the context does not contain the answer, reply exactly: "
        f'"{ABSTAIN_MSG}"\n\n'
        f"Context:\n{context_text}\n\nQuestion: {question}\nAnswer:"
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    answer = resp.choices[0].message.content.strip()
    abstained = ABSTAIN_MSG.lower() in answer.lower()
    return answer, abstained
