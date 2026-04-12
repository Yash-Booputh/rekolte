"""
Seed MongoDB bulletins collection from existing Google Drive PDF files.

Usage:
    python seed_bulletins.py <folder_id> [<folder_id2> ...]

    Or set DRIVE_BULLETINS_FOLDER_ID in .env for a single folder.

The script will:
  1. Recursively list all PDFs under the given Drive folder(s)
  2. Make each file publicly readable (anyone with link can view/download)
  3. Parse filenames → season / week / type
  4. Upsert records into MongoDB bulletins collection (idempotent — safe to re-run)

Prerequisites:
  - MONGODB_URI and GOOGLE_SERVICE_ACCOUNT_JSON in .env
  - The Drive folder(s) must be shared with the service account:
      rekolte-drive-uploader@rekolte-491422.iam.gserviceaccount.com
"""

import re
import sys
import json
import datetime
import os

from dotenv import load_dotenv
load_dotenv()

from pymongo import MongoClient
from googleapiclient.discovery import build
from google.oauth2 import service_account

MONGODB_URI = os.environ["MONGODB_URI"]
SA_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")

client = MongoClient(MONGODB_URI)
db = client["rekolte"]


# ── Drive helpers ─────────────────────────────────────────────────────────────

def get_drive_service():
    if not SA_JSON:
        raise ValueError(
            "GOOGLE_SERVICE_ACCOUNT_JSON not set in .env\n"
            "Paste the full contents of rekolte-491422-3e97a23e3559.json as a "
            "single-line JSON string."
        )
    creds = service_account.Credentials.from_service_account_info(
        json.loads(SA_JSON),
        scopes=["https://www.googleapis.com/auth/drive"],
    )
    return build("drive", "v3", credentials=creds)


def list_pdfs_in_folder(service, folder_id: str) -> list:
    """Recursively list all PDF files under folder_id."""
    results = []
    page_token = None

    while True:
        params = {
            "q": f"'{folder_id}' in parents and trashed = false",
            "fields": "nextPageToken, files(id, name, mimeType)",
            "pageSize": 1000,
        }
        if page_token:
            params["pageToken"] = page_token

        resp = service.files().list(**params).execute()

        for item in resp.get("files", []):
            if item["mimeType"] == "application/vnd.google-apps.folder":
                results.extend(list_pdfs_in_folder(service, item["id"]))
            elif item["name"].lower().endswith(".pdf"):
                results.append(item)

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return results


def make_public(service, file_id: str) -> None:
    """Grant anyone-reader permission (idempotent — Drive ignores duplicates)."""
    try:
        service.permissions().create(
            fileId=file_id,
            body={"type": "anyone", "role": "reader"},
            fields="id",
        ).execute()
    except Exception as e:
        print(f"    ⚠  Could not make {file_id} public: {e}")


# ── Filename parser ───────────────────────────────────────────────────────────

def parse_filename(filename: str) -> dict:
    """Extract season, week, type from a bulletin filename.

    Handled patterns:
      Old (2008-2019):  bul27crop19.pdf  →  week=27, season=2019, type=weekly
      New (2020-2025):  BH-24-23-decembre-2023.pdf  →  week=24, season=2023, type=weekly
      Crop reports:     anything containing 'crop'/'report'/'rapport' + a year
    """
    name = filename.lower()
    if name.endswith(".pdf"):
        name = name[:-4]

    # Old format: bul{week}crop{2-or-4-digit-year}
    m = re.match(r"bul(\d+)crop(\d{2,4})", name)
    if m:
        week = int(m.group(1))
        yr = int(m.group(2))
        season = yr if yr >= 2000 else 2000 + yr
        return {"type": "weekly", "season": season, "week": week}

    # New format: bh-{week}-{day}-{month-name}-{year}
    m = re.match(r"bh-(\d+)-\d+-.+-(\d{4})", name)
    if m:
        return {"type": "weekly", "season": int(m.group(2)), "week": int(m.group(1))}

    # Crop report
    if any(kw in name for kw in ("crop report", "crop_report", "rapport", "annual")):
        m = re.search(r"(20\d{2})", name)
        return {"type": "crop_report", "season": int(m.group(1)) if m else None, "week": None}

    # Fallback: pull year if present
    m = re.search(r"(20\d{2})", name)
    return {"type": "other", "season": int(m.group(1)) if m else None, "week": None}


# ── Main ──────────────────────────────────────────────────────────────────────

def seed(folder_ids: list) -> None:
    service = get_drive_service()

    all_files = []
    for fid in folder_ids:
        print(f"Scanning folder {fid} …")
        found = list_pdfs_in_folder(service, fid)
        print(f"  {len(found)} PDF(s) found")
        all_files.extend(found)

    print(f"\nTotal: {len(all_files)} PDFs — inserting into MongoDB …\n")

    inserted = updated = 0

    for f in all_files:
        file_id = f["id"]
        filename = f["name"]

        make_public(service, file_id)

        parsed = parse_filename(filename)
        doc = {
            "filename": filename,
            "driveFileId": file_id,
            "type": parsed["type"],
            "season": parsed["season"],
            "week": parsed["week"],
            "preview_url": f"https://drive.google.com/file/d/{file_id}/preview",
            "download_url": f"https://drive.google.com/uc?export=download&id={file_id}",
            "uploaded_at": datetime.datetime.utcnow(),
            "uploaded_by": "seed_script",
        }

        result = db.bulletins.update_one(
            {"driveFileId": file_id},
            {"$set": doc},
            upsert=True,
        )

        if result.upserted_id:
            inserted += 1
            print(
                f"  + {filename:<50}  season={str(parsed['season']):<6} "
                f"week={str(parsed['week']):<4}  type={parsed['type']}"
            )
        else:
            updated += 1

    print(f"\nDone. {inserted} inserted, {updated} already existed (refreshed).")


if __name__ == "__main__":
    folder_ids = sys.argv[1:]
    if not folder_ids:
        env_folder = os.environ.get("DRIVE_BULLETINS_FOLDER_ID", "")
        if not env_folder:
            print(__doc__)
            sys.exit(1)
        folder_ids = [env_folder]

    seed(folder_ids)
