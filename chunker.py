"""
Loads markdown docs from corpus/ and splits each into chunks by ## section headers.
Each chunk gets a stable chunk_id: "<doc_slug>::<section_slug>"
"""
import os
import re
import glob

CORPUS_DIR = os.path.join(os.path.dirname(__file__), "corpus")

def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.strip().lower()).strip("-")

def load_chunks():
    chunks = []
    for path in sorted(glob.glob(os.path.join(CORPUS_DIR, "*.md"))):
        doc_slug = os.path.splitext(os.path.basename(path))[0]
        with open(path, "r") as f:
            text = f.read()
        # split on level-2 headers, keep header with its body
        sections = re.split(r"\n(?=## )", text)
        for section in sections:
            section = section.strip()
            if not section or section.startswith("# "):
                # this is the doc title line combined with first section sometimes; handle below
                pass
            header_match = re.match(r"##\s+(.+)", section)
            if not header_match:
                continue
            header = header_match.group(1).strip()
            chunk_id = f"{doc_slug}::{slugify(header)}"
            chunks.append({
                "chunk_id": chunk_id,
                "doc": doc_slug,
                "header": header,
                "text": section,
            })
    return chunks

if __name__ == "__main__":
    chunks = load_chunks()
    print(f"Loaded {len(chunks)} chunks from {len(set(c['doc'] for c in chunks))} documents\n")
    for c in chunks:
        print(c["chunk_id"])
