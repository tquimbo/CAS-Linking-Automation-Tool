import pdfplumber
import re
import pandas as pd

pdf_path = "proposal.pdf"

# 1️⃣ Read PDF text
def read_pdf_text(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

# 2️⃣ Clean numbers with PDF spacing issues
def clean_number(s):
    s = s.replace(" ", "").replace(",", "")
    try:
        return float(s)
    except:
        return None

# 3️⃣ Parse text to extract Item / Volume / Rate / Total
def parse_pdf_text(text):
    pattern = re.compile(r"(.+?)\s+([\d,]+(?:[\s\w%]+)?)\s+\$\s*([\d\s,\.]+)\s+\$\s*([\d\s,\.]+)")
    items = []
    for match in pattern.finditer(text):
        item_name = match.group(1).strip()
        volume = match.group(2).strip()
        rate = clean_number(match.group(3))
        total = clean_number(match.group(4))
        items.append({
            "Item": item_name,
            "Volume": volume,
            "Rate": rate,
            "Total": total
        })
    return items

# 4️⃣ Run everything
pdf_text = read_pdf_text(pdf_path)
parsed_items = parse_pdf_text(pdf_text)

# 5️⃣ Show results
df = pd.DataFrame(parsed_items)
print(df)

# 6️⃣ Optional: save to Excel
df.to_excel("parsed_budget.xlsx", index=False)
print("Saved parsed data to parsed_budget.xlsx")
