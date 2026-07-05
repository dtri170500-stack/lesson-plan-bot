#!/usr/bin/env python3
"""
sync_to_google.py – Upload lesson-plan DOCX files to Google Drive
and write hyperlinks into the correct cells of the schedule Google Sheet.

Usage:
  python3 .agents/skills/lesson_plan_writer/scripts/sync_to_google.py
  python3 .agents/skills/lesson_plan_writer/scripts/sync_to_google.py --age 3-4
"""

import os, sys, re, json, pickle
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
WORKSPACE_ROOT = Path(__file__).resolve().parents[4]

CLIENT_SECRET = WORKSPACE_ROOT / (
    "client_secret_134091499096-akv7egqsiibukpda93m3rcvtn55tbfne"
    ".apps.googleusercontent.com.json"
)
TOKEN_PATH    = WORKSPACE_ROOT / ".agents" / "token.pickle"

OUTPUT_FOLDER = WORKSPACE_ROOT / "Output gi\u00e1o \u00e1n docs"
if not OUTPUT_FOLDER.exists():
    OUTPUT_FOLDER = WORKSPACE_ROOT / "Output giao an docs"
SCHEDULE_PATH = OUTPUT_FOLDER / "_schedule.json"

DRIVE_FOLDER_ID = "1MLJP2IMtGk7d73Zeqv1mT3NGHFdXABTp"
SPREADSHEET_ID  = "16XH3eUo9-WdKxJ0aLjgdQxZ9yoqnqaAQ3YFA2a-yh2k"
SHEET_GID       = 0

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]

# ── Sheet layout (from user's screenshot) ────────────────────────────────────
# Row 3: 2nd week of July, 3-4 YRS  (schedule "Week 1")
# Row 4: 2nd week of July, 5-6 YRS
# Row 5: 3rd week of July, 3-4 YRS  (schedule "Week 2")
# Row 6: 3rd week of July, 5-6 YRS
# Row 7: 4th week of July, 3-4 YRS  (schedule "Week 3")
# Row 8: 4th week of July, 5-6 YRS
WEEK_AGE_ROW = {
    ("Week 1", "3-4"): 3,
    ("Week 1", "5-6"): 4,
    ("Week 2", "3-4"): 5,
    ("Week 2", "5-6"): 6,
    ("Week 3", "3-4"): 7,
    ("Week 3", "5-6"): 8,
}

# Columns (0-indexed, A=0)
# E(4)=SHOW & TELL Mon | F(5)=MATH Tue | G(6)=SHOW & TELL Wed | H(7)=MATH Thu | I(8)=HAPPY FRIDAY Fri
SUBJECT_SESSION_COL = {
    ("Show and Tell", 1): 4,
    ("Math",          1): 5,
    ("Show and Tell", 2): 6,
    ("Math",          2): 7,
    ("Happy Friday",  1): 8,
}

REF_FORMAT_CELL = "D3"  # "THAO, SUE" – used to copy format


def get_credentials():
    creds = None
    if TOKEN_PATH.exists():
        with open(TOKEN_PATH, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        from google.auth.transport.requests import Request
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            from google_auth_oauthlib.flow import InstalledAppFlow
            if not CLIENT_SECRET.exists():
                print(f"[ERROR] Client-secret not found: {CLIENT_SECRET}")
                sys.exit(1)
            flow  = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
            creds = flow.run_local_server(port=0)

        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_PATH, "wb") as f:
            pickle.dump(creds, f)
        print(f"  Token saved -> {TOKEN_PATH}")

    return creds


def upload_file(drive_svc, docx_path: Path, parent_id: str) -> str:
    from googleapiclient.http import MediaFileUpload
    q   = f"'{parent_id}' in parents and name='{docx_path.name}' and trashed=false"
    old = drive_svc.files().list(q=q, fields="files(id)").execute().get("files", [])
    for f in old:
        drive_svc.files().delete(fileId=f["id"]).execute()
        print(f"    Removed stale copy: {docx_path.name}")

    mime  = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    media = MediaFileUpload(str(docx_path), mimetype=mime, resumable=True)
    meta  = {"name": docx_path.name, "parents": [parent_id]}
    file  = drive_svc.files().create(
        body=meta, media_body=media, fields="id,webViewLink"
    ).execute()
    drive_svc.permissions().create(
        fileId=file["id"],
        body={"type": "anyone", "role": "reader"},
    ).execute()
    return file["webViewLink"]


def read_ref_format(sheets_svc):
    try:
        resp = sheets_svc.spreadsheets().get(
            spreadsheetId=SPREADSHEET_ID,
            ranges=[REF_FORMAT_CELL],
            fields="sheets(data(rowData(values(userEnteredFormat))))",
        ).execute()
        return (resp["sheets"][0]["data"][0]["rowData"][0]
                ["values"][0]["userEnteredFormat"])
    except Exception:
        return None


def write_link(sheets_svc, row, col, display_text, url, ref_fmt):
    col_letter = chr(ord("A") + col)
    cell_ref   = f"{col_letter}{row}"

    # Write HYPERLINK formula
    sheets_svc.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=cell_ref,
        valueInputOption="USER_ENTERED",
        body={"values": [[f'=HYPERLINK("{url}","{display_text}")']]},
    ).execute()

    # Build cell format (copy from reference or use sensible default)
    if ref_fmt:
        cell_fmt = {k: v for k, v in ref_fmt.items()
                    if k not in ("backgroundColorStyle", "backgroundColor")}
    else:
        cell_fmt = {
            "textFormat": {"fontFamily": "Comfortaa", "fontSize": 10},
            "horizontalAlignment": "CENTER",
            "verticalAlignment":   "MIDDLE",
            "wrapStrategy":        "WRAP",
        }

    range_spec  = {
        "sheetId": SHEET_GID,
        "startRowIndex": row - 1, "endRowIndex": row,
        "startColumnIndex": col,  "endColumnIndex": col + 1,
    }
    solid_black = {"style": "SOLID", "color": {"red": 0, "green": 0, "blue": 0}}

    sheets_svc.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={"requests": [
            {"repeatCell": {
                "range":  range_spec,
                "cell":   {"userEnteredFormat": cell_fmt},
                "fields": "userEnteredFormat",
            }},
            {"updateBorders": {
                "range":  range_spec,
                "top": solid_black, "bottom": solid_black,
                "left": solid_black, "right": solid_black,
            }},
        ]},
    ).execute()

    print(f"    OK  {cell_ref}  <- {display_text}")


def main(age="3-4"):
    age_key = age.strip()

    if not SCHEDULE_PATH.exists():
        print("[ERROR] _schedule.json not found. Run the pipeline first.")
        sys.exit(1)

    schedule = json.loads(SCHEDULE_PATH.read_text(encoding="utf-8"))["schedule"]

    print("\n==== Step 1: Google OAuth ====")
    print("  A browser window will open – sign in with your Google account.")
    creds = get_credentials()
    from googleapiclient.discovery import build
    drive_svc  = build("drive",  "v3", credentials=creds)
    sheets_svc = build("sheets", "v4", credentials=creds)
    print("  Authenticated OK")

    print("\n==== Step 2: Reading sheet reference format ====")
    ref_fmt = read_ref_format(sheets_svc)
    if ref_fmt:
        tf = ref_fmt.get("textFormat", {})
        print(f"  Font: {tf.get('fontFamily','?')} {tf.get('fontSize','?')}pt, "
              f"align: {ref_fmt.get('horizontalAlignment','?')}")
    else:
        print("  Could not read reference format – using defaults")

    print(f"\n==== Step 3: Building upload plan (age {age_key}) ====")
    lesson_ctrs   = {}
    week_sess_ctrs = {}
    plan = []

    for slot in schedule:
        if slot["status"] != "OK":
            continue
        subj  = slot["subject"]
        week  = slot["week"]
        topic = slot.get("topic", subj)

        lesson_ctrs[subj] = lesson_ctrs.get(subj, 0) + 1
        n = lesson_ctrs[subj]

        wk_key = (week, subj)
        week_sess_ctrs[wk_key] = week_sess_ctrs.get(wk_key, 0) + 1
        session = week_sess_ctrs[wk_key]

        safe_topic = re.sub(r'[\\/:*?"<>|]', "", topic)[:60].strip()
        docx_name  = f"{safe_topic} - Lesson {n}.docx"
        docx_path  = OUTPUT_FOLDER / safe_topic / docx_name

        if not docx_path.exists():
            print(f"  SKIP (file not found): {docx_name}")
            continue

        row = WEEK_AGE_ROW.get((week, age_key))
        col = SUBJECT_SESSION_COL.get((subj, session))

        if row is None:
            print(f"  SKIP (no row): week={week}, age={age_key}")
            continue
        if col is None:
            print(f"  SKIP (no col): {subj} session {session}")
            continue

        plan.append({
            "docx_path":    docx_path,
            "display_text": docx_name.replace(".docx", ""),
            "row": row, "col": col,
            "week": week, "subject": subj,
        })
        print(f"  {docx_name}")
        print(f"    -> cell {chr(ord('A')+col)}{row}  ({week} / {subj} / session {session})")

    if not plan:
        print("\n  Nothing to sync. Check DOCX files exist in the Output folder.")
        return

    print(f"\n==== Step 4: Uploading {len(plan)} file(s) to Google Drive ====")
    for item in plan:
        print(f"\n  Uploading: {item['docx_path'].name}")
        url = upload_file(drive_svc, item["docx_path"], DRIVE_FOLDER_ID)
        item["url"] = url
        print(f"    URL: {url}")

    print(f"\n==== Step 5: Writing links to Google Sheet ====")
    for item in plan:
        write_link(sheets_svc,
                   row=item["row"], col=item["col"],
                   display_text=item["display_text"],
                   url=item["url"], ref_fmt=ref_fmt)

    print(f"\nDone! {len(plan)} lesson plan(s) synced.")
    print(f"Sheet: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")


if __name__ == "__main__":
    age_arg = "3-4"
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--age" and i + 1 < len(args):
            age_arg = args[i + 1]
        elif not a.startswith("--"):
            age_arg = a
    main(age_arg)
