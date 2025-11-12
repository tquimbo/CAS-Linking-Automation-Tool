

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
import pdfplumber, re, pandas as pd

PDF_PATH = "proposal.pdf"

def read_pdf_text(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for p in pdf.pages:
            t = p.extract_text()
            if t:
                text += t + "\n"
    return text

def clean_number(s):
    s = s.replace(" ", "").replace(",", "")
    try:
        return float(s)
    except:
        return None

def extract_qty(volume_str):
    """
    Heuristics for Qty:
      - ignore percentages like '60%'
      - collect numeric tokens (1, 6, 13,700, 21,188, etc.)
      - if any >= 1000, choose the largest (typical volumes)
      - else choose the last numeric (e.g., '6 Hours' -> 6, '1 One-Time' -> 1)
    """
    if not volume_str:
        return None
    s = str(volume_str)

    tokens = re.findall(r"\d[\d,]*(?:\.\d+)?%?", s)
    nums = []
    for tok in tokens:
        if tok.endswith("%"):
            continue
        val = tok.replace(",", "")
        try:
            nums.append(float(val))
        except:
            pass

    if not nums:
        return None

    big = [x for x in nums if x >= 1000]
    if big:
        return max(big)
    return nums[-1]

def parse_pdf_text(text):
    # Matches: <Item> <Volume> $ <Rate> $ <Total>
    pattern = re.compile(r"(.+?)\s+([\d,]+(?:[\s\w%/.,-]+)?)\s+\$\s*([\d\s,\.]+)\s+\$\s*([\d\s,\.]+)")
    rows = []
    for m in pattern.finditer(text):
        item  = m.group(1).strip()
        vol   = m.group(2).strip()
        rate  = clean_number(m.group(3))
        total = clean_number(m.group(4))
        qty   = extract_qty(vol)
        rows.append({"Item": item, "Qty": qty, "Rate": rate, "Total_PDF": total})
    return pd.DataFrame(rows)

def main():
    text = read_pdf_text(PDF_PATH)
    df = parse_pdf_text(text)
    if df.empty:
        print("⚠️ No data extracted. If the PDF is scanned, use OCR first.")
        return

    # Compute difference: Extracted Total − (Qty × Rate)
    df["Calc_Total"] = (df["Qty"] * df["Rate"]).round(2)
    df["Diff"] = (df["Total_PDF"] - df["Calc_Total"]).round(2)

    # Print with Qty & Rate at 4 decimals, totals at 2
    print(f"{'Item':60} {'Qty':>14} {'Rate':>14} {'Total (PDF)':>15} {'Diff (PDF - Q×R)':>18}")
    print("-" * 135)
    for _, r in df.iterrows():
        item = r["Item"][:57] + "..." if len(str(r["Item"])) > 60 else str(r["Item"])
        qty  = 0.0 if pd.isna(r["Qty"]) else r["Qty"]
        rate = 0.0 if pd.isna(r["Rate"]) else r["Rate"]
        tot  = 0.0 if pd.isna(r["Total_PDF"]) else r["Total_PDF"]
        diff = 0.0 if pd.isna(r["Diff"]) else r["Diff"]
        print(f"{item:60} {qty:14,.4f} {rate:14,.4f} {tot:15,.2f} {diff:18,.2f}")

    print("-" * 135)
    print(f"{'SUM TOTALS':60} {'':14} {'':14} "
          f"{df['Total_PDF'].sum(skipna=True):15,.2f} {df['Diff'].sum(skipna=True):18,.2f}")

if __name__ == "__main__":
    main()
