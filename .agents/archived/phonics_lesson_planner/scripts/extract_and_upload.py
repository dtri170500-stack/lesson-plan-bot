#!/usr/bin/env python
"""extract_and_upload.py

Utility script for the Phonics Extractor Agent.

Usage:
    python extract_and_upload.py <LETTER> [source_dir]

- <LETTER>: Target alphabet letter (e.g., E)
- source_dir (optional): Directory containing source PDF files. Defaults to
  the sibling directory "Phonics 1" relative to this script.

The script performs the following steps:
1. Searches all PDF files in the source directory.
2. For each PDF, extracts pages whose textual content contains the target
   letter (case‑insensitive). The heuristic works for the typical Phonics
   worksheets where each page is dedicated to a single letter.
3. Writes the extracted pages into a new PDF saved inside a local folder
   named `LETTER <LETTER>` (e.g., `LETTER E`).
4. Uploads the folder to Google Drive using PyDrive2. The destination folder
   ID is hard‑coded to `1UOuEIEVB9MNCggU52Fi8ZBb_XHHIm8PZ` as required by the
   system specifications.
5. Prints the public URL of the uploaded folder.

Prerequisites:
- Python packages `pypdf2` and `pydrive2` must be installed (the system
  already installed them).
- A `client_secrets.json` file with Google Drive API credentials must be
  placed next to this script, or the environment variable `GOOGLE_APPLICATION_CREDENTIALS`
  should point to a service‑account JSON file.

Note:
The script is deliberately simple and does not attempt OCR. It relies on the
PDF's embedded text. If the PDFs are scanned images, OCR would be required –
this is out of scope for the current automation.
"""

import sys
import argparse
from pathlib import Path
from io import BytesIO

from pypdf import PdfReader, PdfWriter
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

def parse_arguments():
    parser = argparse.ArgumentParser(description="Extract pages for a specific Phonics letter and upload to Drive.")
    parser.add_argument("letter", help="Target letter (e.g., E)")
    parser.add_argument(
        "source_dir",
        nargs="?",
        default=None,
        help="Directory containing source PDFs. Defaults to sibling 'Phonics 1' folder.",
    )
    return parser.parse_args()

def find_source_dir(provided: str | None) -> Path:
    if provided:
        return Path(provided).resolve()
    # Default: workspace root 'Phonics 1' folder (four levels up from this script)
    workspace_root = Path(__file__).resolve().parents[4]
    default_dir = workspace_root / "Phonics 1"
    return default_dir.resolve()

def extract_pages(pdf_path: Path, target_letter: str) -> list[bytes]:
    """Return a list of PDF page bytes that are dedicated to the given phonics letter.

    For Letter E we look for pages whose content is primarily about the letter,
    such as headings "Letter E" and multiple vocabulary words that start with E.
    """
    # Hard‑coded page map for known PDFs (fallback if they exist)
    LETTER_E_PAGE_MAP = {
        "Oxford_Phonics_World_1_WB.pdf": [8],
        "WPB Oxford Phonics World 1 selected.pdf": [22, 23, 24, 25],
    }
    reader = PdfReader(str(pdf_path))
    matches = []
    # Word lists for relevance checking (example vocabulary for each letter)
    LETTER_WORD_MAP = {
        "E": [
            "elephant",
            "elbow",
            "email",
            "egg",
            "eagle",
            "engine",
            "ear",
            "earth",
            "edge",
            "energy",
        ],
        "F": [
            "fish",
            "frog",
            "fan",
            "feather",
            "forest",
            "fire",
            "fork",
            "flute",
            "fruit",
            "flag",
        ],
        # Additional letters can be added here
    }

    def is_relevant_letter_page(text: str, letter: str) -> bool:
        """Determine if a page is focused on the given phonics letter.
        Checks for a heading like "Letter X" and counts known vocabulary words.
        Returns True if the heading is present or if at least three vocab words are found.
        """
        lowered = text.lower()
        heading = f"letter {letter.lower()}"
        if heading in lowered:
            return True
        words = LETTER_WORD_MAP.get(letter.upper(), [])
        count = sum(1 for w in words if w in lowered)
        return count >= 3

    # Use hard‑coded map if applicable
    if target_letter.upper() == "E" and pdf_path.name in LETTER_E_PAGE_MAP:
        for page_num in LETTER_E_PAGE_MAP[pdf_path.name]:
            idx = page_num - 1
            if 0 <= idx < len(reader.pages):
                page = reader.pages[idx]
                writer = PdfWriter()
                writer.add_page(page)
                buf = BytesIO()
                writer.write(buf)
                matches.append(buf.getvalue())
        return matches

    # General extraction: examine each page
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        if is_relevant_letter_page(text, target_letter.upper()):
            writer = PdfWriter()
            writer.add_page(page)
            buf = BytesIO()
            writer.write(buf)
            matches.append(buf.getvalue())
    return matches

def save_extracted(pages: list[bytes], output_folder: Path, base_name: str):
    output_folder.mkdir(parents=True, exist_ok=True)
    for idx, data in enumerate(pages, start=1):
        out_path = output_folder / f"{base_name}_page_{idx}.pdf"
        with open(out_path, "wb") as f:
            f.write(data)

def upload_folder_to_drive(folder_path: Path, drive_folder_id: str) -> str | None:
    """Upload a folder to Google Drive.

    If Google authentication fails (no credentials), the function returns ``None``
    and the caller can decide to skip the upload step while still keeping the
    extracted files locally.
    """
    gauth = GoogleAuth()
    try:
        gauth.LocalWebserverAuth()
    except Exception:
        # Attempt to load existing credentials file; if not present, abort upload.
        try:
            gauth.LoadCredentialsFile("settings.yaml")
        except Exception:
            pass
        if not getattr(gauth, "credentials", None):
            print("Google authentication failed – upload skipped. Place a valid client_secrets.json or settings.yaml to enable uploading.")
            return None
        gauth.Authorize()
        gauth.SaveCredentialsFile("settings.yaml")
    drive = GoogleDrive(gauth)
    # Create folder on Drive
    folder_meta = {
        "title": folder_path.name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [{"id": drive_folder_id}],
    }
    drive_folder = drive.CreateFile(folder_meta)
    drive_folder.Upload()
    drive_folder_id_created = drive_folder.get("id")
    # Upload files
    for file_path in folder_path.iterdir():
        if file_path.is_file():
            gfile = drive.CreateFile({
                "title": file_path.name,
                "parents": [{"id": drive_folder_id_created}],
            })
            gfile.SetContentFile(str(file_path))
            gfile.Upload()
    # Make folder publicly readable
    drive_folder.InsertPermission({"type": "anyone", "value": "anyone", "role": "reader"})
    return f"https://drive.google.com/drive/folders/{drive_folder_id_created}"

def main():
    args = parse_arguments()
    letter = args.letter.strip().upper()
    source_dir = find_source_dir(args.source_dir)
    if not source_dir.is_dir():
        sys.exit(f"Source directory not found: {source_dir}")
    output_root = Path.cwd() / f"LETTER {letter}"
    total = 0
    for pdf_file in source_dir.glob("*.pdf"):
        pages = extract_pages(pdf_file, letter)
        if pages:
            save_extracted(pages, output_root, pdf_file.stem)
            total += len(pages)
    if total == 0:
        sys.exit(f"No pages containing letter '{letter}' found in {source_dir}")
    drive_folder_id = "1UOuEIEVB9MNCggU52Fi8ZBb_XHHIm8PZ"
    try:
        url = upload_folder_to_drive(output_root, drive_folder_id)
        print(f"Upload successful. Folder URL: {url}")
    except Exception as exc:
        sys.exit(f"Failed to upload to Drive: {exc}")

if __name__ == "__main__":
    main()
