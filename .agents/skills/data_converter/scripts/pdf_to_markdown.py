"""
Step 1 – Data Converter
Reads all PDF / DOCX files from the input folder and converts them to Markdown.
Output: markdown_cache/<filename>.md inside the input folder.
"""

import sys, os, json, re
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    os.system(f"{sys.executable} -m pip install pypdf -q")
    from pypdf import PdfReader

try:
    from docx import Document as DocxDocument
except ImportError:
    os.system(f"{sys.executable} -m pip install python-docx -q")
    from docx import Document as DocxDocument

import unicodedata

WORKSPACE_ROOT = Path(__file__).resolve().parents[4]

def find_normalized_dir(parent: Path, name: str) -> Path:
    target_nfc = unicodedata.normalize('NFC', name)
    target_nfd = unicodedata.normalize('NFD', name)
    p_nfc = parent / target_nfc
    if p_nfc.exists():
        return p_nfc
    p_nfd = parent / target_nfd
    if p_nfd.exists():
        return p_nfd
    if parent.exists():
        for child in parent.iterdir():
            if child.is_dir():
                child_norm = unicodedata.normalize('NFC', child.name)
                if child_norm == target_nfc:
                    return child
    return p_nfc

INPUT_FOLDER = find_normalized_dir(WORKSPACE_ROOT, "Nhập học liệu pdf và docs")
if not INPUT_FOLDER.exists():
    INPUT_FOLDER = WORKSPACE_ROOT / "Nhap hoc lieu pdf va docs"

CACHE_FOLDER = INPUT_FOLDER / "markdown_cache"
CACHE_FOLDER.mkdir(exist_ok=True)

def pdf_to_markdown(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    lines  = [f"# {pdf_path.stem}\n"]
    for i, page in enumerate(reader.pages, 1):
        lines.append(f"\n<!-- Page {i} -->\n")
        try:
            text = (page.extract_text() or "").strip()
            lines.append(text if text else "[UNREADABLE_CONTENT]")
        except Exception:
            lines.append("[UNREADABLE_CONTENT]")
    return "\n".join(lines)

def docx_to_markdown(docx_path: Path) -> str:
    doc   = DocxDocument(str(docx_path))
    lines = [f"# {docx_path.stem}\n"]
    for para in doc.paragraphs:
        text  = para.text.strip()
        if not text: continue
        style = para.style.name if para.style else ""
        if   "Heading 1" in style: lines.append(f"# {text}")
        elif "Heading 2" in style: lines.append(f"## {text}")
        elif "Heading 3" in style: lines.append(f"### {text}")
        else:                      lines.append(text)
    return "\n\n".join(lines)

def main():
    files_done = 0
    if not INPUT_FOLDER.exists():
        print(f"  [ERR] Input directory {INPUT_FOLDER} does not exist.")
        return False
    for file in INPUT_FOLDER.iterdir():
        if file.suffix.lower() not in {".pdf", ".docx"}: continue
        if file.stem.startswith("~"): continue
        out = CACHE_FOLDER / f"{file.stem}.md"
        try:
            md = pdf_to_markdown(file) if file.suffix.lower() == ".pdf" else docx_to_markdown(file)
            out.write_text(md, encoding="utf-8")
            print(f"  [OK]  {file.name}  ->  {out.name}")
            files_done += 1
        except Exception as e:
            print(f"  [ERR] {file.name}: {e}")
    print(f"\n[Step 1] {files_done} file(s) converted.")
    return True

if __name__ == "__main__":
    sys.exit(0 if main() else 1)

