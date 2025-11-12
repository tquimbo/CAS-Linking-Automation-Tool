import pdfplumber
with pdfplumber.open("proposal_ocr.pdf") as pdf:
    print(pdf.pages[6].extract_text()[:100000000000])