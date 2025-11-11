#!/usr/bin/env python3
import re, sys
from pathlib import Path

# libs
import fitz  # PyMuPDF
from PyPDF2 import PdfReader
import pdfplumber
from PIL import Image
import pytesseract

PDF = "claim_form.pdf"

# Tweak these to match your label if needed
LABEL_RX = re.compile(r"(class\s*member\s*id|member\s*id|member\s*#|claim(?:\s*|-)id|claim\s*(?:no|number)|id#?)", re.I)
TIGHT_VALUE_RX = re.compile(r"[:#\s]*([A-Za-z0-9\-]{6,40})")
LOOSE_VALUE_RX = re.compile(r"\b[A-Z0-9][A-Z0-9\-]{6,40}\b")

OCR_CONFIG = r'--oem 3 --psm 6 -l eng -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-:#'

def normalize(s: str) -> str:
    return " ".join((s or "").replace("\u00A0", " ").split())

def try_match(text: str):
    if not text: 
        return None
    text = normalize(text)
    # 1) label-based
    for m in LABEL_RX.finditer(text):
        tail = text[m.end(): m.end()+120]
        m2 = TIGHT_VALUE_RX.search(tail)
        if m2 and re.fullmatch(r"[A-Za-z0-9\-]{6,40}", m2.group(1)):
            return m2.group(1)
    # 2) fallback: any ID-like token
    cands = LOOSE_VALUE_RX.findall(text)
    if cands:
        cands = sorted(cands, key=lambda s: (("-" in s), len(s)), reverse=True)
        return cands[0]
    return None

def from_acroform(pdf_path: Path):
    try:
        reader = PdfReader(str(pdf_path))
        if "/AcroForm" in reader.trailer.get("/Root", {}):
            fields = reader.get_fields() or {}
            for name, info in fields.items():
                val = info.get("/V") or info.get("V")
                if val:
                    got = try_match(str(val))
                    if got:
                        return got, f"AcroForm field {name}"
    except Exception:
        pass
    return None, None

def from_pymupdf_text(pdf_path: Path):
    doc = fitz.open(str(pdf_path))
    for i, page in enumerate(doc, start=1):
        # try several extractors
        for mode in ("text", "blocks", "html"):
            try:
                txt = page.get_text(mode)
                got = try_match(txt)
                if got:
                    return got, f"PyMuPDF {mode} page {i}"
            except Exception:
                pass
        # deep: rawdict spans
        try:
            rd = page.get_text("rawdict")
            chunks = []
            for b in rd.get("blocks", []):
                for l in b.get("lines", []):
                    line = "".join([s.get("text","") for s in l.get("spans", [])])
                    chunks.append(line)
            txt = " ".join(chunks)
            got = try_match(txt)
            if got:
                return got, f"PyMuPDF rawdict page {i}"
        except Exception:
            pass
    return None, None

def from_widgets(pdf_path: Path):
    doc = fitz.open(str(pdf_path))
    for i, page in enumerate(doc, start=1):
        if hasattr(page, "widgets"):
            try:
                for w in page.widgets():
                    val = (w.field_value or "") if hasattr(w, "field_value") else ""
                    got = try_match(str(val))
                    if got:
                        return got, f"Widget page {i}"
            except Exception:
                pass
    return None, None

def from_ocr(pdf_path: Path, dpi=300):
    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            im = page.to_image(resolution=dpi).original
            txt = pytesseract.image_to_string(im, config=OCR_CONFIG)
            got = try_match(txt)
            if got:
                return got, f"OCR page {i} ({dpi}dpi)"
    return None, None

def main():
    pdf_path = Path(PDF)
    if not pdf_path.exists():
        print(f"[!] File not found: {pdf_path}")
        sys.exit(1)

    # 1) AcroForm
    val, src = from_acroform(pdf_path)
    if val:
        print(f"{val}  [{src}]")
        return

    # 2) PyMuPDF deep text
    val, src = from_pymupdf_text(pdf_path)
    if val:
        print(f"{val}  [{src}]")
        return

    # 3) Widgets
    val, src = from_widgets(pdf_path)
    if val:
        print(f"{val}  [{src}]")
        return

    # 4) OCR 300 dpi, then 400 dpi
    val, src = from_ocr(pdf_path, dpi=300)
    if val:
        print(f"{val}  [{src}]")
        return
    val, src = from_ocr(pdf_path, dpi=400)
    if val:
        print(f"{val}  [{src}]")
        return

    print("No ID found via any method. If you can paste the exact label line (redacted), I’ll tailor the match.")

if __name__ == "__main__":
    main()

