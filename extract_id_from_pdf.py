#!/usr/bin/env python3
# extract_id_from_pdf.py
# pip install pdfplumber PyPDF2 (optionally: regex chardet)

import re
import json
import sys
import argparse
from pathlib import Path

import pdfplumber
from PyPDF2 import PdfReader

# --- Default pattern ---
# This matches common labels + the ID token (letters/numbers/hyphens, 4–30 chars)
# Examples it will catch:
#   "Class Member ID: ABCD-1234"
#   "ID# 000123"
#   "Member ID 12-345-678"
DEFAULT_PATTERN = r'(?:Class\s*Member\s*ID|Member\s*ID|ID#?|Claim(?:\s*|-)ID)[:\s]*([A-Z0-9\-]{4,30})'

# If you KNOW the exact format, use something stricter, e.g.:
#   r'Class\s*Member\s*ID[:\s]*([0-9]{3}\-[0-9]{3}\-[0-9]{3})'

# --- Helpers ---

def normalize_text(s: str) -> str:
    if not s:
        return ""
    # Replace NBSP and weird spaces with normal space
    s = s.replace("\u00A0", " ").replace("\u2009", " ").replace("\u202F", " ")
    # Join lines to avoid line-break splitting of tokens
    joined = " ".join(s.splitlines())
    # Remove hyphenation at line breaks that may have been preserved
    # (e.g., 'ABC-\n123' -> 'ABC123'; our join already removed '\n', so look for '- ')
    joined = re.sub(r'-\s+', '', joined)
    # Collapse multiple spaces
    joined = re.sub(r'\s+', ' ', joined).strip()
    return joined


def extract_with_pdfplumber(pdf_path: Path, rx: re.Pattern):
    """
    Return a list of dicts: [{"source":"text","page":N,"match":"ABC-123","context":"..."}]
    """
    results = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            raw = page.extract_text() or ""
            text = normalize_text(raw)
            for m in rx.finditer(text):
                token = m.group(1)
                # capture small context around match (optional)
                start = max(m.start() - 40, 0)
                end = min(m.end() + 40, len(text))
                ctx = text[start:end]
                results.append({
                    "source": "text",
                    "page": i,
                    "match": token,
                    "context": ctx
                })
    return results


def extract_from_form_fields(pdf_path: Path, rx: re.Pattern):
    """
    Check AcroForm fields for values that match the pattern.
    Return similar list of dicts, page unknown for fields, set page=None.
    """
    results = []
    try:
        reader = PdfReader(str(pdf_path))
        root = reader.trailer.get("/Root", {})
        if "/AcroForm" in root:
            fields = reader.get_fields()
            if fields:
                for name, info in fields.items():
                    value = (info.get("/V") or info.get("V"))
                    if value:
                        val = normalize_text(str(value))
                        m = rx.search(val)
                        if m:
                            results.append({
                                "source": "form",
                                "page": None,
                                "match": m.group(1),
                                "context": f"Field: {name} = {val}"
                            })
    except Exception:
        # Some PDFs or encrypted docs may error out in PyPDF2; ignore quietly
        pass
    return results


def main():
    ap = argparse.ArgumentParser(
        description="Extract IDs from PDFs using pdfplumber + regex (with optional form-field fallback)."
    )
    ap.add_argument("pdfs", nargs="+", help="Path(s) to PDF file(s)")
    ap.add_argument(
        "--pattern",
        default=DEFAULT_PATTERN,
        help="Regex to capture the ID in group(1). Default matches common 'Class Member ID' styles."
    )
    ap.add_argument(
        "--ignore-case", action="store_true",
        help="Case-insensitive regex (recommended)."
    )
    ap.add_argument(
        "--no-forms", action="store_true",
        help="Disable AcroForm field search."
    )
    ap.add_argument(
        "--first-only", action="store_true",
        help="Stop after the first match per file."
    )
    ap.add_argument(
        "--json", dest="as_json", action="store_true",
        help="Output JSON instead of human-readable text."
    )
    args = ap.parse_args()

    flags = re.IGNORECASE if args.ignore_case else 0
    try:
        rx = re.compile(args.pattern, flags)
    except re.error as e:
        print(f"Invalid regex: {e}", file=sys.stderr)
        sys.exit(2)

    all_outputs = []

    for p in args.pdfs:
        pdf_path = Path(p)
        if not pdf_path.exists():
            print(f"[!] File not found: {pdf_path}", file=sys.stderr)
            continue

        file_results = {
            "file": str(pdf_path),
            "matches": []
        }

        # Text extraction
        text_matches = extract_with_pdfplumber(pdf_path, rx)
        file_results["matches"].extend(text_matches)

        # Optional: form fields
        if not args.no_forms and not (args.first_only and file_results["matches"]):
            field_matches = extract_from_form_fields(pdf_path, rx)
            file_results["matches"].extend(field_matches)

        # If --first-only, keep only the first match (if any)
        if args.first_only and file_results["matches"]:
            file_results["matches"] = [file_results["matches"][0]]

        all_outputs.append(file_results)

    if args.as_json:
        print(json.dumps(all_outputs, indent=2))
        return

    # Pretty print
    for fr in all_outputs:
        print(f"\n=== {fr['file']} ===")
        if not fr["matches"]:
            print("No matches found.")
            continue
        for m in fr["matches"]:
            page = f"page {m['page']}" if m['page'] else "page ?"
            print(f"- {m['match']}  ({m['source']}, {page})")
            # Show a short context line to verify correctness
            ctx = m.get("context", "")
            if ctx:
                if len(ctx) > 140:
                    ctx = ctx[:140] + "…"
                print(f"  context: {ctx}")


if __name__ == "__main__":
    main()
