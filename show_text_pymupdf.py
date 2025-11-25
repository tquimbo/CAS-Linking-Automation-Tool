# import fitz  # PyMuPDF
# doc = fitz.open("claim_form.pdf")
# for i, page in enumerate(doc, start=0):
#     txt = page.get_text("text")  # plain text
#     print(f"\n=== PAGE {i} ===\n{txt if txt.strip() else '(no text)'}")
import re
from pathlib import Path

import pdfplumber
import pytesseract

PDF = "claim_form.pdf"
OCR_CONFIG = r"--oem 3 --psm 6 -l eng"

def main():
    pdf_path = Path(PDF)
    if not pdf_path.exists():
        print(f"[!] File not found: {pdf_path.resolve()}")
        return

    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            img = page.to_image(resolution=300).original
            text = pytesseract.image_to_string(img, config=OCR_CONFIG)

            print(f"\n=== PAGE {i} OCR TEXT ===")
            print(text)
            print("=" * 40)

if __name__ == "__main__":
    main()

