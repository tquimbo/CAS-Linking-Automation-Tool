#!/usr/bin/env python3
import re
from collections import Counter
from pathlib import Path

import pdfplumber
import pytesseract

PDF = "claim_form.pdf"
# Fairly standard OCR config
OCR_CONFIG = r"--oem 3 --psm 6 -l eng"

# Label and value patterns
LABEL_RX = re.compile(r"class\s*member\s*id\s*[:#]?\s*", re.I)
TOKEN_RX = re.compile(r"[A-Z0-9-]{6,40}")  # first token after the label

def extract_ids_from_text(text: str):
    ids = []
    # Normalize whitespace a bit
    t = " ".join((text or "").replace("\u00A0", " ").split())
    # Find every label occurrence
    for m in LABEL_RX.finditer(t):
        tail = t[m.end(): m.end() + 80]  # scan a short window to the right
        m2 = TOKEN_RX.search(tail)
        if m2:
            ids.append(m2.group(0))
    return ids

def main():
    pdf_path = Path(PDF)
    if not pdf_path.exists():
        print(f"[!] File not found: {pdf_path.resolve()}")
        return

    candidates = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            img = page.to_image(resolution=300).original
            text = pytesseract.image_to_string(img, config=OCR_CONFIG)
            page_ids = extract_ids_from_text(text)
            for cid in page_ids:
                candidates.append((i, cid))

    if not candidates:
        print("No Class Member ID found.")
        return

    # Prefer the most frequent token, break ties by length (longer is usually more complete)
    counts = Counter([cid for _, cid in candidates])
    best = sorted(counts.items(), key=lambda kv: (kv[1], len(kv[0])), reverse=True)[0][0]

    print("All candidates (page, id):")
    for p, cid in candidates:
        print(f"  - p{p}: {cid}")
    print(f"\nBest guess: {best}")

if __name__ == "__main__":
    main()
