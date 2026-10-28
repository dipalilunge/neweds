"""Google Sheets storage for public service enquiries, with a local CSV fallback."""
import csv
import os
from datetime import datetime
import config
import supabase_helper

FIELDNAMES = ["Timestamp", "Name", "Email", "Phone", "Service Category", "Service Required", "Message"]
_sheet = None
_attempted = False

def _connect():
    global _sheet, _attempted
    if _sheet is not None:
        return _sheet
    if _attempted:
        return None
    _attempted = True
    creds_path = config.GOOGLE_CREDENTIALS_FILE or ""
    if not config.SERVICES_SHEET_ID or not creds_path or not os.path.exists(creds_path):
        print("[services_helper] Google Sheets credentials not configured; using local CSV fallback.")
        return None
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        client = gspread.authorize(creds)
        book = client.open_by_key(config.SERVICES_SHEET_ID)
        try:
            sheet = book.worksheet(config.SERVICES_WORKSHEET_NAME)
        except gspread.exceptions.WorksheetNotFound:
            # Use an existing imported/default tab if present instead of
            # silently writing into a new tab the owner may not be checking.
            worksheets = book.worksheets()
            if worksheets:
                sheet = worksheets[0]
                print(
                    f"[services_helper] Worksheet {config.SERVICES_WORKSHEET_NAME!r} not found; "
                    f"using existing tab {sheet.title!r}. Set EDS_SERVICES_WORKSHEET to change it."
                )
            else:
                sheet = book.add_worksheet(title=config.SERVICES_WORKSHEET_NAME, rows=1000, cols=len(FIELDNAMES))
        header = sheet.row_values(1)
        if not header:
            sheet.update("A1", [FIELDNAMES])
        elif header != FIELDNAMES:
            raise RuntimeError(
                f"Services worksheet {sheet.title!r} has different headers. "
                "Set EDS_SERVICES_WORKSHEET to the correct tab or align its header row "
                "with the service-enquiry fields before collecting submissions."
            )
        _sheet = sheet
        return _sheet
    except Exception as exc:
        print(f"[services_helper] Google Sheets unavailable; using local CSV fallback: {exc}")
        return None

def save_enquiry(data):
    row = {
        "Timestamp": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z"),
        "Name": data.get("name", "").strip(),
        "Email": data.get("email", "").strip(),
        "Phone": data.get("phone", "").strip(),
        "Service Category": data.get("category", "").strip(),
        "Service Required": data.get("service", "").strip(),
        "Message": data.get("message", "").strip(),
    }
    if supabase_helper.is_configured():
        supabase_helper.request(
            "POST",
            "service_enquiries",
            payload={
                "timestamp": row["Timestamp"],
                "name": row["Name"],
                "email": row["Email"],
                "phone": row["Phone"],
                "service_category": row["Service Category"],
                "service_required": row["Service Required"],
                "message": row["Message"],
            },
        )
        return row

    sheet = _connect()
    if sheet is not None:
        sheet.append_row([row[field] for field in FIELDNAMES], value_input_option="USER_ENTERED")
    else:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config.LOCAL_SERVICE_INQUIRIES_FALLBACK)
        new_file = not os.path.exists(path) or os.path.getsize(path) == 0
        with open(path, "a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
            if new_file:
                writer.writeheader()
            writer.writerow(row)
    return row
