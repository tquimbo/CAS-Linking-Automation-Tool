import re
from pathlib import Path
import pandas as pd
import pdfplumber
from pytesseract import image_to_string

PDF = "proposal.pdf"

# Fast defaults (OCR only as fallback)
OCR_CONFIG = r"--oem 3 --psm 6 -l eng -c preserve_interword_spaces=0"
OCR_DPI = 200
MAX_OCR_PAGES = None

# ---------- numeric spacing fixes ----------
def normalize_numeric_spacing(s: str) -> str:
    if not s: return s
    s = re.sub(r'(?<=\d)\s+(?=[\d.,])', '', s)
    s = re.sub(r'(?<=,)\s+(?=\d)', '', s)
    s = re.sub(r'(?<=\.)\s+(?=\d)', '', s)
    s = re.sub(r'(?<=\d)\s+(?=\.)', '', s)
    s = re.sub(r'(\d)\s+\.(\d)', r'\1.\2', s)
    s = re.sub(r'\.\s+(\d)', r'.\1', s)
    s = re.sub(r'\$\s+(?=\d)', r'$', s)
    s = re.sub(r'(\d)\s+(?=%)', r'\1', s)
    return s

# ---------- money / qty / type ----------
MONEY_RE = re.compile(r'\$\s*([0-9][\d,]*(?:\.\d+)?)')

UNIT_ALTS = [
    r'one[-\s]?time', r'hour(?:s)?',
    r'per\s+email', r'per\s+notice', r'per\s+record', r'per\s+letter', r'per\s+check',
    r'per\s+minute', r'per\s+month', r'per\s+form', r'per\s+payment', r'per\s+mailing',
    r'per\s+state', r'per\s+scan', r'per\s+piece', r'per\s+trace', r'per\s+response',
    r'per\s+fax', r'per\s+text', r'per\s+call', r'per\s+request'
]
# capture number + unit; keep spans so we can remove exactly from the title
UNIT_RE = re.compile(r'(?P<num>[0-9][\d,]*(?:\.\d+)?)\s*(?P<unit>(' + '|'.join(UNIT_ALTS) + r'))\b', re.I)

def _to_float(s: str):
    try: return float(s.replace(",", ""))
    except: return None

def find_rate_total(line: str):
    amts = [(m.start(), m.group(1)) for m in MONEY_RE.finditer(line)]
    if len(amts) < 2: return None, None
    total_val = _to_float(amts[-1][1])  # rightmost
    rate_val  = _to_float(amts[-2][1])  # second-rightmost
    return rate_val, total_val

def extract_qty_type_and_spans(left_side: str):
    """
    Find ALL '<num> <unit>' matches; return:
      - qty (from LAST match), type (normalized)
      - spans list of (start, end) to remove from item text (so '9,695 Per Trace' is removed)
    Naked trailing numbers (e.g., '... Campaign 1') are ignored by design.
    """
    spans = []
    matches = list(UNIT_RE.finditer(left_side))
    if not matches:
        return None, None, spans
    # remove ALL qty+unit phrases from the title later
    for m in matches:
        spans.append((m.start(), m.end()))
    last = matches[-1]
    qty = _to_float(last.group('num').replace(",", ""))
    u_raw = last.group('unit')
    utype = normalize_unit(u_raw)
    return qty, utype, spans

def normalize_unit(u: str) -> str:
    u = u.lower().strip().replace('one time','one-time')
    u = re.sub(r'\s+',' ', u)
    return u

# ---------- parse helpers ----------
def parse_lines(lines):
    rows = []
    for ln in lines:
        rate, total = find_rate_total(ln)
        if rate is None or total is None:
            continue

        # everything left of the first $
        first_dollar = ln.find('$')
        left = ln[:first_dollar].strip() if first_dollar != -1 else ln

        # qty/type + exact spans to remove from the title
        qty, utype, spans = extract_qty_type_and_spans(left)

        # Clean item: remove ALL qty+unit spans (in reverse order so indices stay valid)
        item = left
        for s, e in sorted(spans, key=lambda x: x[0], reverse=True):
            item = (item[:s] + item[e:]).strip()

        # keep trailing numbers like "... Campaign 1" in the item (we only removed qty+unit pairs)
        # final whitespace/punctuation cleanup
        item = re.sub(r'\s{2,}', ' ', item)
        item = item.strip(' -,:;')

        rows.append({
            "Item": item,
            "Quantity": qty,
            "Type": utype,
            "Rate": rate,
            "Total_PDF": total,
            "Diff": round(total - (qty or 0) * (rate or 0), 2)
        })
    return pd.DataFrame(rows)

def parse_via_text(pdf_path: str):
    lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            t = normalize_numeric_spacing(t)
            for ln in t.splitlines():
                ln = ln.strip()
                if ln: lines.append(ln)
    return parse_lines(lines)

def parse_via_ocr(pdf_path: str, dpi=OCR_DPI, max_pages=MAX_OCR_PAGES):
    lines = []
    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
        pages = range(total) if max_pages is None else range(min(total, max_pages))
        for i in pages:
            print(f"OCR page {i+1}/{total} @ {dpi}dpi ...")
            img = pdf.pages[i].to_image(resolution=dpi).original
            raw = image_to_string(img, config=OCR_CONFIG)
            norm = normalize_numeric_spacing(raw)
            for ln in norm.splitlines():
                ln = ln.strip()
                if ln: lines.append(ln)
    return parse_lines(lines)

# ---------- main ----------
def main():
    pdf_path = Path(PDF)
    if not pdf_path.exists():
        print(f"[!] File not found: {pdf_path.resolve()}")
        return

    # fast path
    df = parse_via_text(str(pdf_path))
    if len(df) < 3:
        print("Falling back to OCR (this can take a bit)...")
        df = parse_via_ocr(str(pdf_path))

    if df.empty:
        print("No rows parsed with rate & total.")
        return

    # Pretty print
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

    out = Path("ocr_parsed_summary.csv")
    df.to_csv(out, index=False)
    print(f"\nSaved details to {out.resolve()}")

if __name__ == "__main__":
    main()
