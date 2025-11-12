

# import pdfplumber, re, pandas as pd

# PDF_PATH = "proposal.pdf"

# def read_pdf_text(pdf_path):
#     text = ""
#     with pdfplumber.open(pdf_path) as pdf:
#         for p in pdf.pages:
#             t = p.extract_text()
#             if t:
#                 text += t + "\n"
#     return text

# def clean_number(s):
#     s = s.replace(" ", "").replace(",", "")
#     try:
#         return float(s)
#     except:
#         return None

# def extract_qty(volume_str):
#     """Get first numeric quantity from the volume section"""
#     if not volume_str: return None
#     m = re.search(r"[\d,]+(?:\.\d+)?", volume_str.replace(",", ""))
#     return float(m.group()) if m else None

# def parse_pdf_text(text):
#     pattern = re.compile(r"(.+?)\s+([\d,]+(?:[\s\w%/.,-]+)?)\s+\$\s*([\d\s,\.]+)\s+\$\s*([\d\s,\.]+)")
#     rows = []
#     for m in pattern.finditer(text):
#         item  = m.group(1).strip()
#         vol   = m.group(2).strip()
#         rate  = clean_number(m.group(3))
#         total = clean_number(m.group(4))
#         qty   = extract_qty(vol)
#         rows.append({"Item": item, "Qty": qty, "Rate": rate, "Total_PDF": total})
#     return pd.DataFrame(rows)

# def main():
#     text = read_pdf_text(PDF_PATH)
#     df = parse_pdf_text(text)
#     if df.empty:
#         print("⚠️ No data extracted. Check if PDF text is machine-readable.")
#         return

#     df["Calc_Total"] = (df["Qty"] * df["Rate"]).round(2)

#     print(f"{'Item':60} {'Qty':>10} {'Rate':>10} {'Total (PDF)':>15} {'Qty×Rate':>15}")
#     print("-" * 115)
#     for _, r in df.iterrows():
#         item = r["Item"][:57] + "..." if len(r["Item"]) > 60 else r["Item"]
#         print(f"{item:60} {r['Qty']:10,.2f} {r['Rate']:10,.2f} {r['Total_PDF']:15,.2f} {r['Calc_Total']:15,.2f}")

#     print("-" * 115)
#     print(f"{'SUM TOTALS':60} {'':10} {'':10} {df['Total_PDF'].sum():15,.2f} {df['Calc_Total'].sum():15,.2f}")

# if __name__ == "__main__":
#     main()
# import pdfplumber, re, pandas as pd

# PDF_PATH = "proposal.pdf"

# def read_pdf_text(pdf_path):
#     text = ""
#     with pdfplumber.open(pdf_path) as pdf:
#         for p in pdf.pages:
#             t = p.extract_text()
#             if t:
#                 text += t + "\n"
#     return text

# def clean_number(s):
#     s = s.replace(" ", "").replace(",", "")
#     try:
#         return float(s)
#     except:
#         return None

# def extract_qty(volume_str):
#     """
#     Heuristics for Qty:
#       - ignore percentages like '60%'
#       - collect numeric tokens (1, 6, 13,700, 21,188, etc.)
#       - if any >= 1000, choose the largest (typical volumes)
#       - else choose the last numeric (e.g., '6 Hours' -> 6, '1 One-Time' -> 1)
#     """
#     if not volume_str:
#         return None
#     s = str(volume_str)

#     tokens = re.findall(r"\d[\d,]*(?:\.\d+)?%?", s)
#     nums = []
#     for tok in tokens:
#         if tok.endswith("%"):
#             continue
#         val = tok.replace(",", "")
#         try:
#             nums.append(float(val))
#         except:
#             pass

#     if not nums:
#         return None

#     big = [x for x in nums if x >= 1000]
#     if big:
#         return max(big)
#     return nums[-1]

# def parse_pdf_text(text):
#     # Matches: <Item> <Volume> $ <Rate> $ <Total>
#     pattern = re.compile(r"(.+?)\s+([\d,]+(?:[\s\w%/.,-]+)?)\s+\$\s*([\d\s,\.]+)\s+\$\s*([\d\s,\.]+)")
#     rows = []
#     for m in pattern.finditer(text):
#         item  = m.group(1).strip()
#         vol   = m.group(2).strip()
#         rate  = clean_number(m.group(3))
#         total = clean_number(m.group(4))
#         qty   = extract_qty(vol)
#         rows.append({"Item": item, "Qty": qty, "Rate": rate, "Total_PDF": total})
#     return pd.DataFrame(rows)

# def main():
#     text = read_pdf_text(PDF_PATH)
#     df = parse_pdf_text(text)
#     if df.empty:
#         print("⚠️ No data extracted. If the PDF is scanned, use OCR first.")
#         return

#     # Compute difference: Extracted Total − (Qty × Rate)
#     df["Calc_Total"] = (df["Qty"] * df["Rate"]).round(2)
#     df["Diff"] = (df["Total_PDF"] - df["Calc_Total"]).round(2)

#     # Print with Qty & Rate at 4 decimals, totals at 2
#     print(f"{'Item':60} {'Qty':>14} {'Rate':>14} {'Total (PDF)':>15} {'Diff (PDF - Q×R)':>18}")
#     print("-" * 135)
#     for _, r in df.iterrows():
#         item = r["Item"][:57] + "..." if len(str(r["Item"])) > 60 else str(r["Item"])
#         qty  = 0.0 if pd.isna(r["Qty"]) else r["Qty"]
#         rate = 0.0 if pd.isna(r["Rate"]) else r["Rate"]
#         tot  = 0.0 if pd.isna(r["Total_PDF"]) else r["Total_PDF"]
#         diff = 0.0 if pd.isna(r["Diff"]) else r["Diff"]
#         print(f"{item:60} {qty:14,.4f} {rate:14,.4f} {tot:15,.2f} {diff:18,.2f}")

#     print("-" * 135)
#     print(f"{'SUM TOTALS':60} {'':14} {'':14} "
#           f"{df['Total_PDF'].sum(skipna=True):15,.2f} {df['Diff'].sum(skipna=True):18,.2f}")

# if __name__ == "__main__":
#     main()
import re
import pdfplumber
import pytesseract
from pytesseract import image_to_string
from pathlib import Path
import pandas as pd

PDF = "proposal.pdf"

# OCR settings: LSTM engine, block of text. The "preserve_interword_spaces=0" helps reduce random spaces.
OCR_CONFIG = r"--oem 3 --psm 6 -l eng -c preserve_interword_spaces=0"

# ---------- 1) Fix Tesseract's spacing inside numbers ----------
def normalize_numeric_spacing(s: str) -> str:
    if not s:
        return s
    # Remove spaces within numeric runs (digit/comma/dot)
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

# ---------- 2) Money extraction (rightmost two = Rate, Total) ----------
MONEY_RE = re.compile(r'\$\s*([0-9][\d,]*(?:\.\d+)?)')

def find_rate_total(line: str):
    """Return (rate, total) from the rightmost two $ amounts; None if not present."""
    amounts = [(m.start(), m.group(1)) for m in MONEY_RE.finditer(line)]
    if len(amounts) < 2:
        return None, None
    # Rightmost = total, second-rightmost = rate
    total_val = _to_float(amounts[-1][1])
    rate_val  = _to_float(amounts[-2][1])
    return rate_val, total_val

def _to_float(s: str):
    try:
        return float(s.replace(",", ""))
    except Exception:
        return None

# ---------- 3) Quantity + Type: "the number just before a unit word" ----------
# Define unit phrases you expect to see; tweak/extend as needed
UNIT_ALTS = [
    r'one[-\s]?time', r'hour(?:s)?', r'per\s+email', r'per\s+notice', r'per\s+record', r'per\s+letter',
    r'per\s+check', r'per\s+minute', r'per\s+month', r'per\s+form', r'per\s+payment', r'per\s+mailing',
    r'per\s+state', r'per\s+scan', r'per\s+piece', r'per\s+trace', r'per\s+response', r'per\s+fax',
    r'per\s+text', r'per\s+call', r'per\s+request'
]
UNIT_RE = re.compile(
    r'(?P<num>[0-9][\d,]*(?:\.\d+)?)\s*(?P<unit>(' + '|'.join(UNIT_ALTS) + r'))\b',
    flags=re.IGNORECASE
)

def extract_qty_and_type(left_side: str):
    """
    Search the text to the LEFT of the money columns for the pattern:
      <number> <unit>
    and return (qty, type). If multiple matches, take the LAST one (closest to money columns).
    If no match, return (None, None).
    """
    matches = list(UNIT_RE.finditer(left_side))
    if matches:
        m = matches[-1]
        num = _to_float(m.group('num').replace(",", ""))
        u_raw = m.group('unit').lower()
        u_norm = normalize_unit(u_raw)
        return num, u_norm
    # fallback: try a plain number (ignore percents)
    nums = [n for n in re.findall(r'[0-9][\d,]*(?:\.\d+)?%?', left_side) if not n.endswith('%')]
    if nums:
        return _to_float(nums[-1].replace(",", "")), None
    return None, None

def normalize_unit(u: str) -> str:
    u = u.lower().strip()
    u = u.replace('  ', ' ')
    u = u.replace('one time', 'one-time')
    # Normalize "per  X" spacing
    u = re.sub(r'\s+', ' ', u)
    return u

# ---------- 4) Main OCR→parse ----------
def ocr_lines_from_pdf(pdf_path: str):
    lines = []
    p = Path(pdf_path)
    if not p.exists():
        raise FileNotFoundError(f"PDF not found: {p.resolve()}")
    with pdfplumber.open(str(p)) as pdf:
        for page in pdf.pages:
            # OCR the rendered image of the page
            img = page.to_image(resolution=300).original
            raw = image_to_string(img, config=OCR_CONFIG)
            norm = normalize_numeric_spacing(raw)
            # Split into lines and keep non-empty ones
            for ln in norm.splitlines():
                ln = ln.strip()
                if ln:
                    lines.append(ln)
    return lines

def parse_lines(lines):
    rows = []
    for ln in lines:
        rate, total = find_rate_total(ln)
        if rate is None or total is None:
            continue  # not a charge row
        # Left side (for item/qty/type) = everything before the first dollar sign
        first_dollar = ln.find('$')
        left_side = ln[:first_dollar].strip() if first_dollar != -1 else ln

        qty, utype = extract_qty_and_type(left_side)

        # "Item" is the left_side with the qty+unit snippet removed (for readability)
        item = left_side
        if qty is not None and utype:
            # try to remove the last occurrence of "<qty> <unit>"
            pat = re.compile(rf'{re.escape(str(int(qty) if qty.is_integer() else str(qty)))}\s*{re.escape(utype)}', re.IGNORECASE)
            item = pat.sub('', item).strip()

        rows.append({
            "Item": item,
            "Quantity": qty,
            "Type": utype,
            "Rate": rate,
            "Total_PDF": total,
            "Diff": round(total - (qty or 0) * (rate or 0), 2)
        })
    return pd.DataFrame(rows)

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

def main():
    lines = ocr_lines_from_pdf(PDF)
    df = parse_lines(lines)
    print_table(df)
    # Also save CSV for inspection
    out = Path("ocr_parsed_summary.csv")
    df.to_csv(out, index=False)
    print(f"\nSaved details to {out.resolve()}")

if __name__ == "__main__":
    main()
