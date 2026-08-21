import os
import io

import config


def _save_locally(src_path, filename):
    out_dir = os.path.join(os.path.dirname(__file__), "recordings")
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, filename)
    try:
        # prefer moving if same filesystem else copy
        from shutil import copyfile

        copyfile(src_path, dst)
    except Exception:
        try:
            with open(src_path, "rb") as r, open(dst, "wb") as w:
                w.write(r.read())
        except Exception:
            return None
    return dst


def upload_recording(local_path, filename):
    """Upload recording to Google Drive when configured, otherwise save locally.

    Returns a dict with keys: `success` (bool), `path` (local path or drive file id),
    and `error` (optional).
    """
    # If Drive config not set or credentials missing, fall back to local save.
    creds_file = os.path.abspath(config.GOOGLE_CREDENTIALS_FILE or "")
    folder_id = config.DRIVE_INTERVIEW_FOLDER_ID or ""

    if not folder_id or not os.path.exists(creds_file):
        saved = _save_locally(local_path, filename)
        return {"success": bool(saved), "path": saved or local_path}

    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        scopes = ["https://www.googleapis.com/auth/drive.file"]
        creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
        service = build("drive", "v3", credentials=creds, cache_discovery=False)

        media = MediaFileUpload(local_path, mimetype="audio/webm")
        file_metadata = {"name": filename, "parents": [folder_id]}
        f = service.files().create(body=file_metadata, media_body=media, fields="id,name").execute()
        return {"success": True, "path": f.get("id")}
    except Exception as exc:
        # on failure, save locally
        saved = _save_locally(local_path, filename)
        return {"success": False, "path": saved or local_path, "error": str(exc)}
