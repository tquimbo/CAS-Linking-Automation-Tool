# import pdfplumber
# from pathlib import Path

# PDF_PATH = Path("claim_form.pdf")

# if not PDF_PATH.exists():
#     print(f"❌ File not found: {PDF_PATH.resolve()}")
#     exit()

# with pdfplumber.open(PDF_PATH) as pdf:
#     for i, page in enumerate(pdf.pages, start=1):
#         text = page.extract_text() or ""
#         print(f"\n=== PAGE {i} ===")
#         if not text.strip():
#             print("(No text extracted from this page — might be an image or scanned document)")
#         else:
#             print(text)
import pdfplumber

with pdfplumber.open("claim_form.pdf") as pdf:
    for i, page in enumerate(pdf.pages, start=1):
        text = page.extract_text() or ""
        print(f"\n=== PAGE {i} ===\n{text}")

