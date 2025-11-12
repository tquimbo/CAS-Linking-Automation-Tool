# import pdfplumber
# import pytesseract
# from pathlib import Path

# PDF = "proposal.pdf"

# # OCR settings: English, automatic layout
# OCR_CONFIG = r"--oem 3 --psm 6 -l eng"

# pdf_path = Path(PDF)
# if not pdf_path.exists():
#     print(f"[!] File not found: {pdf_path.resolve()}")
#     exit()

# with pdfplumber.open(str(pdf_path)) as pdf:
#     for i, page in enumerate(pdf.pages, start=1):
#         # Render each page as an image
#         image = page.to_image(resolution=300).original
#         # OCR the image
#         text = pytesseract.image_to_string(image, config=OCR_CONFIG)
#         print(f"\n=== PAGE {i} (visible text via OCR) ===\n")
#         if text.strip():
#             print(text.strip())
#         else:
#             print("(No visible text detected)")
import re
import pdfplumber
import pytesseract
from pathlib import Path

PDF = "proposal.pdf"

# OCR settings: LSTM, block of text, English
# preserve_interword_spaces=0 helps Tesseract avoid inserting extra spaces
OCR_CONFIG = r"--oem 3 --psm 6 -l eng -c preserve_interword_spaces=0"

def normalize_numeric_spacing(s: str) -> str:
    if not s:
        return s
    # 1) Remove spaces between digits / commas / dots within numeric runs
    #    e.g. "1 50 .00" -> "150.00", "2 ,250" -> "2,250"
    s = re.sub(r'(?<=\d)\s+(?=[\d.,])', '', s)          # digit SP digit/comma/dot
    s = re.sub(r'(?<=,)\s+(?=\d)', '', s)               # comma SP digit
    s = re.sub(r'(?<=\.)\s+(?=\d)', '', s)              # dot SP digit
    s = re.sub(r'(?<=\d)\s+(?=\.)', '', s)              # digit SP dot

    # 2) Fix "0 .005" -> "0.005" and ". 005" -> ".005"
    s = re.sub(r'(\d)\s+\.(\d)', r'\1.\2', s)           # "0 .005" -> "0.005"
    s = re.sub(r'\.\s+(\d)', r'.\1', s)                 # ". 005" -> ".005"

    # 3) Tighten dollar signs: "$ 1 50.00" -> "$150.00"
    s = re.sub(r'\$\s+(?=[\d])', r'$', s)               # "$ 150" -> "$150"

    # 4) Collapse accidental spaces inside pe
