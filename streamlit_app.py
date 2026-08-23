import streamlit as st

import config
import portal_storage
import sheets_helper

st.set_page_config(page_title="Engineering Design Studio", page_icon="🏫", layout="wide")


def _course_by_name(name):
    target = (name or "").strip().lower()
    return next((c for c in config.COURSES if c["name"].strip().lower() == target), None)


def render_home():
    st.title(config.INSTITUTE["name"])
    st.caption(config.INSTITUTE["tagline"])

    st.write(config.INSTITUTE["address"])
    st.write(f"Phone: {config.INSTITUTE['phone']} | Email: {config.INSTITUTE['email']} | Hours: {config.INSTITUTE['hours']}")

    for note in config.NOTIFICATIONS:
        st.info(note)

    st.subheader("Courses")
    for track_name in ["Mechanical Design", "IT & Software", "Civil Design", "Electrical Design"]:
        track_courses = [c for c in config.COURSES if c["track"] == track_name]
        if not track_courses:
            continue
        st.markdown(f"### {track_name}")
        cols = st.columns(3)
        for idx, course in enumerate(track_courses):
            with cols[idx % 3]:
                st.markdown(f"**{course['name']}**")
                st.write(f"Duration: {course['duration']}")
                st.write(f"Fee: ₹{course['fee']}")
                drive_url = config.DRIVE_NOTES_LINKS.get(course["id"], "#")
                st.markdown(f"[Open Drive]({drive_url})")


def render_admin_login():
    if st.session_state.get("admin_logged_in"):
        render_admin_dashboard()
        return

    st.subheader("Admin Login")
    with st.form("admin_login_form"):
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        if password == config.ADMIN_PASSWORD:
            st.session_state.admin_logged_in = True
            st.rerun()
        else:
            st.error("Incorrect admin password.")


def render_admin_dashboard():
    st.subheader("Admin Dashboard")
    if st.button("Logout"):
        st.session_state.admin_logged_in = False
        st.rerun()

    batches = portal_storage.get_batches()
    admissions = sheets_helper.get_recent_admissions(limit=20)

    st.markdown("### Create Batch")
    with st.form("batch_form"):
        course_id = st.selectbox("Course", [c["id"] for c in config.COURSES], format_func=lambda cid: next(c["name"] for c in config.COURSES if c["id"] == cid))
        batch_name = st.text_input("Batch Name")
        start_date = st.date_input("Start Date")
        fee = st.number_input("Fee", min_value=0, step=1)
        submitted = st.form_submit_button("Create Batch")

    if submitted:
        portal_storage.add_batch(course_id, batch_name, str(start_date), int(fee))
        st.success(f"Batch created for {course_id}.")
        st.rerun()

    st.markdown("### Upload Content")
    if batches:
        with st.form("content_form"):
            batch = st.selectbox("Batch", batches, format_func=lambda b: f"{b['name']} — {b['course_id']}")
            content_type = st.selectbox("Type", ["notes", "assessment"])
            title = st.text_input("Title")
            link = st.text_input("External Link")
            uploaded_file = st.file_uploader("File Upload")
            content_submitted = st.form_submit_button("Publish Content")

        if content_submitted:
            if title and (link or uploaded_file):
                portal_storage.save_content(batch["course_id"], batch["id"], content_type, title, uploaded_file, link)
                st.success("Content published.")
            else:
                st.warning("Title and either a file or link are required.")

    st.markdown("### Admission Records")
    if admissions:
        st.dataframe(admissions, use_container_width=True)
    else:
        st.info("No admissions recorded yet.")

    st.markdown("### Teacher Reviews")
    submissions = portal_storage.get_submissions()
    if submissions:
        with st.form("review_form"):
            submission = st.selectbox(
                "Submission",
                [f"{item['student_name']} — {item['title']} ({item['submission_id']})" for item in submissions],
            )
            selected = next(item for item in submissions if f"{item['student_name']} — {item['title']} ({item['submission_id']})" == submission)
            teacher_name = st.text_input("Teacher Name", value="Teacher")
            review_status = st.selectbox("Status", ["Reviewed", "Needs Revision", "Approved"])
            teacher_review = st.text_area("Review")
            review_submitted = st.form_submit_button("Save Review")

        if review_submitted:
            if teacher_review.strip():
                portal_storage.add_review(selected["submission_id"], teacher_name, teacher_review, review_status)
                st.success("Review saved.")
            else:
                st.warning("A review is required.")

        for item in submissions:
            reviews = portal_storage.get_reviews(item.get("submission_id"))
            if reviews:
                st.markdown(f"#### {item['student_name']} — {item['title']}")
                for review in reviews:
                    st.write(f"- {review.get('teacher')} [{review.get('status')}] {review.get('reviewed_at')}: {review.get('review')}")
    else:
        st.info("No student submissions available for review yet.")

    st.markdown("### Batches")
    if batches:
        st.dataframe(batches, use_container_width=True)
    else:
        st.info("No batches created yet.")


def render_student_login():
    if st.session_state.get("student_logged_in"):
        render_student_portal()
        return

    st.subheader("Student Login")
    with st.form("student_login_form"):
        student_name = st.text_input("Student Name")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        if password == config.STUDENT_PASSWORD and sheets_helper.is_name_admitted(student_name):
            st.session_state.student_logged_in = True
            st.session_state.student_name = student_name
            st.rerun()
        else:
            st.error("Invalid student details.")


def render_student_portal():
    st.subheader("Student Portal")
    if st.button("Logout"):
        st.session_state.student_logged_in = False
        st.session_state.student_name = ""
        st.rerun()

    student_name = st.session_state.get("student_name", "")
    record = sheets_helper.get_admission_for_name(student_name)
    if not record:
        st.warning("No admission record found for this student name.")
        return

    course_name = record.get("Course Name", "")
    course = _course_by_name(course_name)
    if not course:
        st.warning("Course not matched in current catalog.")
        return

    batch_id = str(record.get("Batch ID", ""))
    batch = next((b for b in portal_storage.get_batches() if b.get("id") == batch_id), None)
    if not batch:
        st.warning("Batch mapping not found for this student record.")
        return

    drive_url = config.DRIVE_NOTES_LINKS.get(course["id"], "#")
    st.success(f"Welcome {record.get('Student Name', student_name)} — {course_name}")
    st.markdown(f"[Open Course Drive Folder]({drive_url})")

    content_items = portal_storage.get_content(course["id"], batch["id"])
    if content_items:
        st.markdown("### Course Notes & Assessments")
        for item in content_items:
            label = f"{item['type'].title()} — {item['title']}"
            if item.get("link"):
                st.markdown(f"- [{label}]({item['link']})")
            elif item.get("relative_path"):
                st.markdown(f"- {label} — [Download]({item['relative_path']})")
            else:
                st.markdown(f"- {label}")
    else:
        st.info("No notes or assessments have been published for this batch yet.")


pages = {
    "Home": render_home,
    "Admin": render_admin_login,
    "Student": render_student_login,
}

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "student_logged_in" not in st.session_state:
    st.session_state.student_logged_in = False
if "student_name" not in st.session_state:
    st.session_state.student_name = ""

st.sidebar.title("Navigation")
choice = st.sidebar.radio("Go to", list(pages.keys()))
pages[choice]()
