"""
Step 5 v3 – Google Workspace Sync via Service Account
Upload DOCX len Google Drive + Ghi hyperlink vao Google Sheet
Khong dung GAS, khong can browser, token khong bao gio expire.
"""

import sys, os, json, re
from pathlib import Path

# Auto-install dependencies
for pkg in ["google-api-python-client", "google-auth"]:
    try:
        if "google" in pkg:
            import googleapiclient
    except ImportError:
        os.system(f"{sys.executable} -m pip install {pkg} -q")

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
CONFIG_PATH    = WORKSPACE_ROOT / ".agents" / "config.json"
SA_KEY_PATH    = WORKSPACE_ROOT / ".agents" / "service_account.json"  # <-- Bạn đặt file key tại đây
OUTPUT_FOLDER  = WORKSPACE_ROOT / "Output gi\u00e1o \u00e1n docs"
if not OUTPUT_FOLDER.exists():
    OUTPUT_FOLDER = WORKSPACE_ROOT / "Output giao an docs"

with open(CONFIG_PATH, encoding="utf-8") as f:
    cfg = json.load(f)

DRIVE_FOLDER_ID  = cfg.get("drive_folder_id", "")
SPREADSHEET_ID   = cfg.get("spreadsheet_id", "")

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]

# Cot mapping theo layout Sheet:
# E=5(idx4): Show&Tell Mon | F=6(idx5): Math Tue | G=7(idx6): Show&Tell Wed
# H=8(idx7): Math Thu      | I=9(idx8): Happy Fri
COLUMN_MAP = {
    ("Show and Tell", 1): 5,
    ("Math",          1): 6,
    ("Show and Tell", 2): 7,
    ("Math",          2): 8,
    ("Happy Friday",  1): 9,
}

def get_credentials():
    if not SA_KEY_PATH.exists():
        print(f"\n[Step 5] SETUP REQUIRED: Service Account key file not found.")
        print(f"  Expected at: {SA_KEY_PATH}")
        print(f"\n  How to create (5 minutes, free):")
        print(f"  1. Go to: https://console.cloud.google.com/")
        print(f"  2. Create a project -> Enable 'Google Drive API' and 'Google Sheets API'")
        print(f"  3. Go to IAM & Admin -> Service Accounts -> Create Service Account")
        print(f"  4. Download JSON key -> rename to 'service_account.json'")
        print(f"  5. Place the file at: {SA_KEY_PATH}")
        print(f"  6. Share Drive folder + Sheet with the service account email in the JSON file")
        sys.exit(1)
    creds = service_account.Credentials.from_service_account_file(str(SA_KEY_PATH), scopes=SCOPES)
    return creds

def detect_subject(stem):
    low = stem.lower()
    if "math" in low: return "Math"
    if "happy" in low or "friday" in low: return "Happy Friday"
    return "Show and Tell"

def detect_lesson_num(filename):
    m = re.search(r"Lesson\s+(\d+)", filename, re.IGNORECASE)
    return int(m.group(1)) if m else 1

def upload_to_drive(drive_svc, docx_path: Path, age: str, week: str) -> str:
    """Upload DOCX to Age subfolder, return file URL."""
    # Find or create Age subfolder
    q = f"'{DRIVE_FOLDER_ID}' in parents and name='Age {age}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = drive_svc.files().list(q=q, fields="files(id,name)").execute()
    folders = results.get("files", [])
    if folders:
        folder_id = folders[0]["id"]
    else:
        meta = {"name": f"Age {age}", "mimeType": "application/vnd.google-apps.folder", "parents": [DRIVE_FOLDER_ID]}
        folder = drive_svc.files().create(body=meta, fields="id").execute()
        folder_id = folder["id"]

    # Delete old file with same name
    q2 = f"'{folder_id}' in parents and name='{docx_path.name}' and trashed=false"
    old = drive_svc.files().list(q=q2, fields="files(id)").execute().get("files", [])
    for f in old:
        drive_svc.files().delete(fileId=f["id"]).execute()

    # Upload new file
    media = MediaFileUpload(str(docx_path), mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document", resumable=True)
    meta = {"name": docx_path.name, "parents": [folder_id]}
    file = drive_svc.files().create(body=meta, media_body=media, fields="id,webViewLink").execute()

    # Make it public
    drive_svc.permissions().create(fileId=file["id"], body={"type": "anyone", "role": "reader"}).execute()
    return file["webViewLink"]

def write_link_to_sheet(sheets_svc, week: str, age: str, subject: str, display_text: str, url: str, lesson_num: int):
    """Write hyperlink to correct cell with Comfortaa formatting."""
    # Get sheet data to find the target row
    result = sheets_svc.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range="A:J"
    ).execute()
    values = result.get("values", [])
    
    # Find target column (1-indexed)
    col = COLUMN_MAP.get((subject, lesson_num), COLUMN_MAP.get((subject, 1), 5))
    
    # Find target row: match age in col B (index 1)
    age_clean = re.sub(r"[^0-9-]", "", age)
    week_num  = 2 if "2" in week else 1
    count     = 0
    target_row = -1
    for i, row in enumerate(values):
        cell_val = row[1] if len(row) > 1 else ""
        if age_clean in str(cell_val):
            count += 1
            if count == week_num:
                target_row = i + 1  # 1-indexed
                break
    
    if target_row == -1:
        return f"WARNING: Row not found for [Age {age}][Week {week_num}]"
    
    # Convert col number to A1 notation
    col_letter = chr(ord("A") + col - 1)
    cell_ref   = f"{col_letter}{target_row}"
    
    # Write hyperlink formula
    formula = f'=HYPERLINK("{url}","{display_text}")'
    sheets_svc.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=cell_ref,
        valueInputOption="USER_ENTERED",
        body={"values": [[formula]]}
    ).execute()
    
    # Format: Comfortaa 12, center, wrap, black border
    sheet_id = 0
    requests_body = {"requests": [
        {"repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": target_row-1, "endRowIndex": target_row, "startColumnIndex": col-1, "endColumnIndex": col},
            "cell": {"userEnteredFormat": {
                "textFormat": {"fontFamily": "Comfortaa", "fontSize": 12},
                "horizontalAlignment": "CENTER",
                "verticalAlignment": "MIDDLE",
                "wrapStrategy": "WRAP"
            }},
            "fields": "userEnteredFormat(textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"
        }},
        {"updateBorders": {
            "range": {"sheetId": sheet_id, "startRowIndex": target_row-1, "endRowIndex": target_row, "startColumnIndex": col-1, "endColumnIndex": col},
            "top":    {"style": "SOLID", "color": {"red": 0, "green": 0, "blue": 0}},
            "bottom": {"style": "SOLID", "color": {"red": 0, "green": 0, "blue": 0}},
            "left":   {"style": "SOLID", "color": {"red": 0, "green": 0, "blue": 0}},
            "right":  {"style": "SOLID", "color": {"red": 0, "green": 0, "blue": 0}},
        }}
    ]}
    sheets_svc.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=requests_body).execute()
    return f"OK at {cell_ref} (row={target_row}, col={col})"

def main(age: str):
    creds      = get_credentials()
    drive_svc  = build("drive",  "v3", credentials=creds)
    sheets_svc = build("sheets", "v4", credentials=creds)
    
    # Load schedule for week and subject mapping
    sched_path = OUTPUT_FOLDER / "_schedule.json"
    schedule   = []
    if sched_path.exists():
        schedule = json.loads(sched_path.read_text(encoding="utf-8")).get("schedule", [])
    
    file_metadata = {}
    lesson_counters = {}
    for slot in schedule:
        if slot["status"] != "OK":
            continue
        subj = slot["subject"]
        lesson_counters[subj] = lesson_counters.get(subj, 0) + 1
        n = lesson_counters[subj]
        
        topic = slot.get("topic", subj)
        safe_topic = re.sub(r'[\\/:*?"<>|]', '', topic)[:60].strip()
        expected_filename = f"{safe_topic} - Lesson {n}.docx"
        file_metadata[expected_filename.lower()] = {
            "week": slot["week"],
            "subject": subj,
            "lesson_num": n
        }

    docx_files = sorted(OUTPUT_FOLDER.rglob("*.docx"))
    if not docx_files:
        print("[Step 5] No DOCX files found. Run Step 4 first.")
        return False

    total_ok = 0
    for docx in docx_files:
        meta = file_metadata.get(docx.name.lower())
        if meta:
            week       = meta["week"]
            subject    = meta["subject"]
            lesson_num = meta["lesson_num"]
        else:
            subject    = detect_subject(docx.stem)
            lesson_num = detect_lesson_num(docx.name)
            week       = "Week 1"
        
        print(f"\n  Uploading: {docx.name}  ({week} / {subject} Lesson {lesson_num})")
        try:
            url = upload_to_drive(drive_svc, docx, age, week)
            print(f"  Drive: {url}")
            msg = write_link_to_sheet(sheets_svc, week, age, subject, docx.stem, url, lesson_num)
            print(f"  Sheet: {msg}")
            total_ok += 1
        except Exception as e:
            print(f"  [ERR] {e}")
    
    print(f"\n[Step 5] Done: {total_ok}/{len(docx_files)} uploaded.")
    return total_ok > 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python upload_to_drive.py <age>")
        sys.exit(1)
    sys.exit(0 if main(sys.argv[1]) else 1)
