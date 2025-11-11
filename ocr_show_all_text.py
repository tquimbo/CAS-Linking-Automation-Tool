import pdfplumber
import pytesseract
from pathlib import Path

PDF = "proposal.pdf"

# OCR settings: English, automatic layout
OCR_CONFIG = r"--oem 3 --psm 6 -l eng"

pdf_path = Path(PDF)
if not pdf_path.exists():
    print(f"[!] File not found: {pdf_path.resolve()}")
    exit()

with pdfplumber.open(str(pdf_path)) as pdf:
    for i, page in enumerate(pdf.pages, start=1):
        # Render each page as an image
        image = page.to_image(resolution=300).original
        # OCR the image
        text = pytesseract.image_to_string(image, config=OCR_CONFIG)
        print(f"\n=== PAGE {i} (visible text via OCR) ===\n")
        if text.strip():
            print(text.strip())
        else:
            print("(No visible text detected)")
