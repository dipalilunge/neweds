# Engineering Design Studio — web app

A Flask + HTML/CSS site for the institute, with:

- **Homepage** — courses, HR and IT service cards, a service enquiry form, address/contact with an embedded map, and a keyword-based FAQ assistant.
- **Admin dashboard** (`/admin`) — password-protected form to record admissions (student name, course, fee, Aadhar number, college, mobile, address, placement details) in Supabase, Google Sheets, or a local CSV fallback.
- **Student portal** (`/student`) — password-protected page listing every course with a button that opens that course's Google Drive notes folder in a new tab.

## 1. Run it locally

```bash
cd eds_app
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Visit `http://localhost:5000`.

Default passwords (change these — see step 3):
- Admin: `eds@admin123`
- Student: `eds@student123`

Without database or Google setup, admin submissions save to `admissions_local.csv` in the project folder, and student notes links show `#` placeholders. Everything else works out of the box.

## 2. Connect Supabase (admissions and service enquiries)

The app can store admissions and service enquiries in a Supabase PostgreSQL database without requiring Google Sheets API credentials.

1. Create a Supabase project.
2. In Supabase **SQL Editor**, run the schema in [`supabase_schema.sql`](./supabase_schema.sql).
3. In **Project Settings -> API**, copy the project URL and `service_role` secret.
4. Set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in the deployment environment. Keep the service role key server-side and secret.
5. Submit test records and verify them in the `admissions` and `service_enquiries` tables.

If Supabase is not configured, the existing Google Sheets integration is still used when its credentials are available, otherwise the app falls back to local CSV files. Local CSV files are not durable on Render's default ephemeral filesystem.

## 3. Connect Google Sheets (optional alternative)

1. In [Google Cloud Console](https://console.cloud.google.com/), create a project (or reuse one) and enable the **Google Sheets API** and **Google Drive API**.
2. Create a **Service Account**, then create a JSON key for it and download it.
3. Save that file as `google_credentials.json` inside the `eds_app` folder (same level as `app.py`). Keep it private — never commit it to a public repo.
4. Create a Google Sheet for admissions. Share it with the service account's email address (found inside the JSON file, looks like `xxxx@xxxx.iam.gserviceaccount.com`) with **Editor** access.
5. Copy the Sheet ID from its URL:
   `https://docs.google.com/spreadsheets/d/`**`THIS_PART_IS_THE_ID`**`/edit`
6. The project is preconfigured with your admissions spreadsheet ID (`1YBCkcWHIPdDpakjIm3J8hB_WRlLT8NxoY6nzde6CtIE`). If you deploy on Render, ensure `EDS_ADMISSIONS_SHEET_ID` is set to this same ID. The worksheet tab defaults to `Admissions`; set `EDS_ADMISSIONS_WORKSHEET` if your tab has a different name. To change the ID manually, open `config.py` and set:
   ```python
   ADMISSIONS_SHEET_ID = "1YBCkcWHIPdDpakjIm3J8hB_WRlLT8NxoY6nzde6CtIE"
   ```
7. Restart the app. The admin dashboard shows which storage backend is active. If credentials are missing, it falls back to the local CSV and prints a note in the terminal.

## 4. Connect Google Sheets (service enquiries)

The service enquiry form is configured to use the spreadsheet ID supplied for this project, with a separate worksheet named `Service Inquiries`. It does not replace or change the admissions spreadsheet. To enable writes, share that spreadsheet with the same Google service-account email used by the app, granting **Editor** access. Configure `EDS_GOOGLE_CREDENTIALS_JSON` (recommended on Render) or place the service-account key in `google_credentials.json`. The app creates the `Service Inquiries` worksheet and header row if needed. If Google credentials are not configured or the sheet is inaccessible, submissions are stored in `service_inquiries_local.csv` as a local fallback. On Render's default ephemeral filesystem, that fallback is not durable across redeploys.

Optional environment variables:

```bash
EDS_SERVICES_SHEET_ID=1RVHEUbSoEpmUX3u3JIjcRI8uPt3O2VBCVvkU26yIjpM
EDS_SERVICES_WORKSHEET="Service Inquiries"
```

## 5. Connect Google Drive (course notes)

1. Create one Drive folder per course (Python, SQL, C++, Java, Data Science, Data Analytics, AI, CATIA, Creo, SolidWorks, AutoCAD).
2. Set each folder's sharing to **"Anyone with the link — Viewer"** (or share individually with students, if you'd rather keep them private).
3. Copy each folder's link and paste it into `config.py` inside `DRIVE_NOTES_LINKS`, matching the course `id` keys already listed there.

## 6. Change the passwords and secret key

Set these as environment variables before running in anything other than a local demo:

```bash
export EDS_SECRET_KEY="a-long-random-string"
export EDS_ADMIN_PASSWORD="something-only-staff-know"
export EDS_STUDENT_PASSWORD="something-shared-with-enrolled-students"
```

Or edit the defaults directly in `config.py`.

## 7. Edit institute details, courses and FAQ answers

All editable content — address, phone, email, hours, course list, fees, placement stats, notification banner text, and FAQ answers — lives in `config.py`. No template or Python logic needs to change to update any of it.

## 8. Deploying

For real use, run behind a production WSGI server (e.g. `gunicorn app:app`) rather than `python app.py`, put it behind HTTPS, and set the environment variables from step 4. Consider giving each course batch its own student password if you want tighter access control.

### Deploy on Render

1. Push this folder to GitHub and create a new **Blueprint** in Render, selecting the repository. Render will read `render.yaml` and create the web service.
2. In the service environment, enter values for `EDS_ADMIN_PASSWORD`, `EDS_STUDENT_PASSWORD`, `SUPABASE_URL`, and `SUPABASE_SERVICE_ROLE_KEY`.
3. Deploy. Render provides the `PORT` value automatically, and the configured Gunicorn command binds to it.

The default Render filesystem is ephemeral. Admissions and service enquiries use Supabase when configured, but locally stored users, batches, course uploads, interview recordings, and fallback CSV data can disappear on redeploy. Move those features to persistent storage before relying on them for production records.

## Project structure

```
eds_app/
  app.py                  Flask routes
  config.py                All editable content & settings
  sheets_helper.py         Google Sheets read/write with local CSV fallback
  requirements.txt
  templates/
    base.html
    index.html             Homepage
    admin_login.html
    admin_dashboard.html
    student_login.html
    student.html
    partials/gear.svg
  static/
    css/style.css
    js/main.js
    js/faq.js
    images/logo.jpg
```
