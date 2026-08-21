import json
import os
import uuid
from datetime import datetime

from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BATCHES_FILE = os.path.join(BASE_DIR, "batches.json")
WORK_DIR = os.path.join(BASE_DIR, "student_work")
WORK_INDEX_FILE = os.path.join(WORK_DIR, "submissions.json")


def _read_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return default


def _write_json(path, value):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)


def get_batches():
    return _read_json(BATCHES_FILE, [])


def add_batch(course_id, name, start_date, fee):
    batches = get_batches()
    batch = {
        "id": uuid.uuid4().hex[:10],
        "course_id": course_id,
        "name": name,
        "start_date": start_date,
        "fee": fee,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    batches.append(batch)
    _write_json(BATCHES_FILE, batches)
    return batch


def save_submission(student, course_id, title, uploaded_file):
    filename = secure_filename(uploaded_file.filename or "work")
    extension = os.path.splitext(filename)[1]
    stored_name = f"{uuid.uuid4().hex}{extension}"
    os.makedirs(WORK_DIR, exist_ok=True)
    uploaded_file.save(os.path.join(WORK_DIR, stored_name))

    submissions = _read_json(WORK_INDEX_FILE, [])
    submission = {
        "student_name": student.get("name", ""),
        "student_email": student.get("email", ""),
        "course_id": course_id,
        "title": title,
        "filename": filename,
        "stored_name": stored_name,
        "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    submissions.append(submission)
    _write_json(WORK_INDEX_FILE, submissions)
    return submission


def get_submissions(student_email=None):
    submissions = _read_json(WORK_INDEX_FILE, [])
    if student_email:
        submissions = [s for s in submissions if s.get("student_email") == student_email]
    return list(reversed(submissions))


def submission_path(stored_name):
    safe_name = secure_filename(stored_name)
    path = os.path.join(WORK_DIR, safe_name)
    return path if os.path.isfile(path) else None
