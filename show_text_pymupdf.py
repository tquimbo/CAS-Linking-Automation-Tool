import fitz  # PyMuPDF
doc = fitz.open("proposal.pdf")
for i, page in enumerate(doc, start=1):
    txt = page.get_text("text")  # plain text
    print(f"\n=== PAGE {i} ===\n{txt if txt.strip() else '(no text)'}")
