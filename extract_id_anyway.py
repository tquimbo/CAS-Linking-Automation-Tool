#!/usr/bin/env python3
# import re, sys
# from pathlib import Path

# # libs
# import fitz  # PyMuPDF
# from PyPDF2 import PdfReader
# import pdfplumber
# from PIL import Image
# import pytesseract

# PDF = "claim_form.pdf"

# # Tweak these to match your label if needed
# LABEL_RX = re.compile(r"(class\s*member\s*id|member\s*id|member\s*#|claim(?:\s*|-)id|claim\s*(?:no|number)|id#?)", re.I)
# TIGHT_VALUE_RX = re.compile(r"[:#\s]*([A-Za-z0-9\-]{6,40})")
# LOOSE_VALUE_RX = re.compile(r"\b[A-Z0-9][A-Z0-9\-]{6,40}\b")

# OCR_CONFIG = r'--oem 3 --psm 6 -l eng -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-:#'

# def normalize(s: str) -> str:
#     return " ".join((s or "").replace("\u00A0", " ").split())

# def try_match(text: str):
#     if not text: 
#         return None
#     text = normalize(text)
#     # 1) label-based
#     for m in LABEL_RX.finditer(text):
#         tail = text[m.end(): m.end()+120]
#         m2 = TIGHT_VALUE_RX.search(tail)
#         if m2 and re.fullmatch(r"[A-Za-z0-9\-]{6,40}", m2.group(1)):
#             return m2.group(1)
#     # 2) fallback: any ID-like token
#     cands = LOOSE_VALUE_RX.findall(text)
#     if cands:
#         cands = sorted(cands, key=lambda s: (("-" in s), len(s)), reverse=True)
#         return cands[0]
#     return None

# def from_acroform(pdf_path: Path):
#     try:
#         reader = PdfReader(str(pdf_path))
#         if "/AcroForm" in reader.trailer.get("/Root", {}):
#             fields = reader.get_fields() or {}
#             for name, info in fields.items():
#                 val = info.get("/V") or info.get("V")
#                 if val:
#                     got = try_match(str(val))
#                     if got:
#                         return got, f"AcroForm field {name}"
#     except Exception:
#         pass
#     return None, None

# def from_pymupdf_text(pdf_path: Path):
#     doc = fitz.open(str(pdf_path))
#     for i, page in enumerate(doc, start=1):
#         # try several extractors
#         for mode in ("text", "blocks", "html"):
#             try:
#                 txt = page.get_text(mode)
#                 got = try_match(txt)
#                 if got:
#                     return got, f"PyMuPDF {mode} page {i}"
#             except Exception:
#                 pass
#         # deep: rawdict spans
#         try:
#             rd = page.get_text("rawdict")
#             chunks = []
#             for b in rd.get("blocks", []):
#                 for l in b.get("lines", []):
#                     line = "".join([s.get("text","") for s in l.get("spans", [])])
#                     chunks.append(line)
#             txt = " ".join(chunks)
#             got = try_match(txt)
#             if got:
#                 return got, f"PyMuPDF rawdict page {i}"
#         except Exception:
#             pass
#     return None, None

# def from_widgets(pdf_path: Path):
#     doc = fitz.open(str(pdf_path))
#     for i, page in enumerate(doc, start=1):
#         if hasattr(page, "widgets"):
#             try:
#                 for w in page.widgets():
#                     val = (w.field_value or "") if hasattr(w, "field_value") else ""
#                     got = try_match(str(val))
#                     if got:
#                         return got, f"Widget page {i}"
#             except Exception:
#                 pass
#     return None, None

# def from_ocr(pdf_path: Path, dpi=300):
#     with pdfplumber.open(str(pdf_path)) as pdf:
#         for i, page in enumerate(pdf.pages, start=1):
#             im = page.to_image(resolution=dpi).original
#             txt = pytesseract.image_to_string(im, config=OCR_CONFIG)
#             got = try_match(txt)
#             if got:
#                 return got, f"OCR page {i} ({dpi}dpi)"
#     return None, None

# def main():
#     pdf_path = Path(PDF)
#     if not pdf_path.exists():
#         print(f"[!] File not found: {pdf_path}")
#         sys.exit(1)

#     # 1) AcroForm
#     val, src = from_acroform(pdf_path)
#     if val:
#         print(f"{val}  [{src}]")
#         return

#     # 2) PyMuPDF deep text
#     val, src = from_pymupdf_text(pdf_path)
#     if val:
#         print(f"{val}  [{src}]")
#         return

#     # 3) Widgets
#     val, src = from_widgets(pdf_path)
#     if val:
#         print(f"{val}  [{src}]")
#         return

#     # 4) OCR 300 dpi, then 400 dpi
#     val, src = from_ocr(pdf_path, dpi=300)
#     if val:
#         print(f"{val}  [{src}]")
#         return
#     val, src = from_ocr(pdf_path, dpi=400)
#     if val:
#         print(f"{val}  [{src}]")
#         return

#     print("No ID found via any method. If you can paste the exact label line (redacted), I’ll tailor the match.")

# if __name__ == "__main__":
#     main()

##break

import re
from pathlib import Path
import pandas as pd
import pdfplumber
import pytesseract
from pytesseract import image_to_string

PDF = "proposal.pdf"

# OCR settings: LSTM engine, block of text.
# preserve_interword_spaces=0 helps reduce random inner-digit spaces.
OCR_CONFIG = r"--oem 3 --psm 6 -l eng -c preserve_interword_spaces=0"

# ------------ 1) Fix Tesseract's spacing inside numbers ------------
def normalize_numeric_spacing(s: str) -> str:
    if not s:
        return s
    # Remove spaces inside numeric runs (digit/comma/dot)
    s = re.sub(r'(?<=\d)\s+(?=[\d.,])', '', s)
    s = re.sub(r'(?<=,)\s+(?=\d)', '', s)
    s = re.sub(r'(?<=\.)\s+(?=\d)', '', s)
    s = re.sub(r'(?<=\d)\s+(?=\.)', '', s)
    # Fix "0 .005" -> "0.005" and ". 005" -> ".005"
    s = re.sub(r'(\d)\s+\.(\d)', r'\1.\2', s)
    s = re.sub(r'\.\s+(\d)', r'.\1', s)
    # Tighten dollar signs: "$ 1 50.00" -> "$150.00"
    s = re.sub(r'\$\s+(?=\d)', r'$', s)
    # Collapse spaces before % like "6 0%" -> "60%"
    s = re.sub(r'(\d)\s+(?=%)', r'\1', s)
    return s

# ------------ 2) Money extraction (two rightmost $ = rate, total) ------------
MONEY_RE = re.compile(r'\$\s*([0-9][\d,]*(?:\.\d+)?)')

def _to_float(s: str):
    try:
        return float(s.replace(",", ""))
    except Exception:
        return None

def find_rate_total(line: str):
    amounts = [(m.start(), m.group(1)) for m in MONEY_RE.finditer(line)]
    if len(amounts) < 2:
        return None, None
    total_val = _to_float(amounts[-1][1])  # rightmost
    rate_val  = _to_float(amounts[-2][1])  # second-rightmost
    return rate_val, total_val

# ------------ 3) Quantity + Type (only when number is directly followed by a unit) ------------
UNIT_ALTS = [
    r'one[-\s]?time',
    r'hour(?:s)?',
    r'per\s+email', r'per\s+notice', r'per\s+record', r'per\s+letter', r'per\s+check',
    r'per\s+minute', r'per\s+month', r'per\s+form', r'per\s+payment', r'per\s+mailing',
    r'per\s+state', r'per\s+scan', r'per\s+piece', r'per\s+trace', r'per\s+response',
    r'per\s+fax', r'per\s+text', r'per\s+call', r'per\s+request'
]
UNIT_RE = re.compile(
    r'(?P<num>[0-9][\d,]*(?:\.\d+)?)\s*(?P<unit>(' + '|'.join(UNIT_ALTS) + r'))\b',
    flags=re.IGNORECASE
)

def normalize_unit(u: str) -> str:
    u = u.lower().strip()
    u = u.replace('  ', ' ')
    u = u.replace('one time', 'one-time')
    u = re.sub(r'\s+', ' ', u)  # collapse spaces ("per    email" -> "per email")
    return u

def extract_qty_and_type(left_side: str):
    """
    Capture quantity ONLY when it's immediately followed by a recognized unit phrase.
    This prevents trailing numbers like "...Campaign 1" from being treated as quantity.
    """
    matches = list(UNIT_RE.finditer(left_side))
    if matches:
        m = matches[-1]  # closest to money columns
        num = _to_float(m.group('num').replace(",", ""))
        u_raw = m.group('unit')
        return num, normalize_unit(u_raw)

    # Fallback ONLY if a number is followed by a minimal unit keyword (per/hours/one-time).
    # This still avoids orphan numbers like "Campaign 1".
    fallback = re.search(
        r'([0-9][\d,]*(?:\.\d+)?)\s*(one[-\s]?time|per\s+\w+|hour(?:s)?)\b',
        left_side, flags=re.IGNORECASE
    )
    if fallback:
        num = _to_float(fallback.group(1).replace(",", ""))
        unit = fallback.group(2)
        return num, normalize_unit(unit)

    return None, None

# ------------ 4) OCR lines from PDF ------------
def ocr_lines_from_pdf(pdf_path: str):
    lines = []
    p = Path(pdf_path)
    if not p.exists():
        raise FileNotFoundError(f"PDF not found: {p.resolve()}")
    with pdfplumber.open(str(p)) as pdf:
        total_pages = len(pdf.pages)
        for i, page in enumerate(pdf.pages, start=1):
            print(f"OCR processing page {i}/{total_pages}...")
            img = page.to_image(resolution=300).original
            raw = image_to_string(img, config=OCR_CONFIG)
            norm = normalize_numeric_spacing(raw)
            for ln in norm.splitlines():
                ln = ln.strip()
                if ln:
                    lines.append(ln)
    return lines

# ------------ 5) Parse rows ------------
def parse_lines(lines):
    rows = []
    for ln in lines:
        rate, total = find_rate_total(ln)
        if rate is None or total is None:
            continue  # not a charge row
        # Left side = everything before the first $
        first_dollar = ln.find('$')
        left_side = ln[:first_dollar].strip() if first_dollar != -1 else ln

        qty, utype = extract_qty_and_type(left_side)

        # Item is the left_side; do NOT treat trailing numbers (like "Campaign 1") as qty.
        # If we found a "<qty><unit>" pair, remove only that segment from the item for readability.
        item = left_side
        if qty is not None and utype:
            # Build a flexible pattern that matches the last occurrence of "<qty> <unit>"
            qty_str = f"{int(qty)}" if qty is not None and float(qty).is_integer() else str(qty)
            unit_pat = re.escape(utype).replace(r'\ ', r'\s+')
            pair_pat = re.compile(rf'({re.escape(qty_str)}\s*{unit_pat})\b', flags=re.IGNORECASE)
            # remove only the last occurrence
            matches = list(pair_pat.finditer(item))
            if matches:
                m = matches[-1]
                item = (item[:m.start()] + item[m.end():]).strip()

        rows.append({
            "Item": item,
            "Quantity": qty,
            "Type": utype,
            "Rate": rate,
            "Total_PDF": total,
            "Diff": round(total - (qty or 0) * (rate or 0), 2)
        })
    return pd.DataFrame(rows)

# ------------ 6) Pretty print ------------
def print_table(df: pd.DataFrame):
    if df.empty:
        print("No rows parsed with rate & total.")
        return
    print(f"{'Item':60} {'Qty':>14} {'Type':>16} {'Rate':>14} {'Total (PDF)':>15} {'Diff':>12}")
    print("-" * 135)
    for _, r in df.iterrows():
        item = (str(r['Item'])[:57] + '...') if len(str(r['Item'])) > 60 else str(r['Item'])
        qty  = 0.0 if pd.isna(r['Quantity']) else r['Quantity']
        typ  = r['Type'] or ''
        rate = 0.0 if pd.isna(r['Rate']) else r['Rate']
        tot  = 0.0 if pd.isna(r['Total_PDF']) else r['Total_PDF']
        diff = 0.0 if pd.isna(r['Diff']) else r['Diff']
        print(f"{item:60} {qty:14,.4f} {typ:>16} {rate:14,.4f} {tot:15,.2f} {diff:12,.2f}")
    print("-" * 135)
    print(f"{'SUMS':60} {'':14} {'':16} {'':14} {df['Total_PDF'].sum(skipna=True):15,.2f} {df['Diff'].sum(skipna=True):12,.2f}")

# ------------ 7) Main ------------
def main():
    lines = ocr_lines_from_pdf(PDF)
    df = parse_lines(lines)
    print_table(df)
    out = Path("ocr_parsed_summary.csv")
    df.to_csv(out, index=False)
    print(f"\nSaved details to {out.resolve()}")

if __name__ == "__main__":
    main()
