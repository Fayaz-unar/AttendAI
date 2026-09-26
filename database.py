import sqlite3
import os
import uuid
import qrcode
from datetime import datetime

DB_FOLDER = "database"
DB_FILE = os.path.join(DB_FOLDER, "attendai.db")
QR_FOLDER = "qrcodes"


def create_database():
    """Create the database, tables, and folders if they don't already exist."""
    os.makedirs(DB_FOLDER, exist_ok=True)
    os.makedirs(QR_FOLDER, exist_ok=True)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_number TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            semester INTEGER NOT NULL,
            qr_token TEXT UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT DEFAULT 'Present',
            FOREIGN KEY (student_id) REFERENCES students(student_id),
            UNIQUE(student_id, date)
        )
    """)

    conn.commit()
    conn.close()


def get_connection():
    return sqlite3.connect(DB_FILE)


# ---------------------------------------------------------------------------
# Students
# ---------------------------------------------------------------------------

def register_student(name, roll_number, department, semester):
    """Insert a new student, generate their QR token + image.

    Returns (qr_path, student_id) on success, or (None, error_message) on failure.
    """
    qr_token = str(uuid.uuid4())
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO students (name, roll_number, department, semester, qr_token)
            VALUES (?, ?, ?, ?, ?)
        """, (name, roll_number, department, semester, qr_token))
        student_id = cursor.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return None, "Roll number already exists."
    conn.close()

    os.makedirs(QR_FOLDER, exist_ok=True)
    qr_image = qrcode.make(qr_token)
    qr_path = os.path.join(QR_FOLDER, f"{roll_number}.png")
    qr_image.save(qr_path)

    return qr_path, student_id


def get_all_students(search=None, department=None, semester=None):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT student_id, name, roll_number, department, semester, qr_token FROM students WHERE 1=1"
    params = []

    if search:
        query += " AND (name LIKE ? OR roll_number LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    if department and department != "All":
        query += " AND department = ?"
        params.append(department)
    if semester and semester != "All":
        query += " AND semester = ?"
        params.append(semester)

    query += " ORDER BY roll_number"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_departments():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT department FROM students ORDER BY department")
    rows = [r[0] for r in cursor.fetchall()]
    conn.close()
    return rows


def delete_student(student_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT roll_number FROM students WHERE student_id = ?", (student_id,))
    row = cursor.fetchone()

    cursor.execute("DELETE FROM attendance WHERE student_id = ?", (student_id,))
    cursor.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
    conn.commit()
    conn.close()

    if row:
        qr_path = os.path.join(QR_FOLDER, f"{row[0]}.png")
        if os.path.exists(qr_path):
            os.remove(qr_path)


def get_student_by_token(qr_token):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT student_id, name, roll_number, department, semester
        FROM students WHERE qr_token = ?
    """, (qr_token,))
    row = cursor.fetchone()
    conn.close()
    return row


def get_student_by_roll(roll_number):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT student_id, name, roll_number, department, semester
        FROM students WHERE roll_number = ?
    """, (roll_number,))
    row = cursor.fetchone()
    conn.close()
    return row


def get_department_distribution():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT department, COUNT(*) FROM students GROUP BY department")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_weekly_trend():
    """Present count per day for the last 7 days (including today), with
    days that have no attendance filled in as 0 so the chart never breaks."""
    from datetime import datetime, timedelta

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT date, COUNT(*) FROM attendance
        WHERE date >= date('now', '-6 days')
        GROUP BY date
    """)
    rows = dict(cursor.fetchall())
    conn.close()

    today = datetime.now().date()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    return [(d.strftime("%a"), rows.get(d.strftime("%Y-%m-%d"), 0)) for d in days]


# ---------------------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------------------

def mark_attendance(student_id):
    """Mark a student present for today. Returns (True, time) or (False, message)."""
    today = datetime.now().strftime("%Y-%m-%d")
    now_time = datetime.now().strftime("%H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO attendance (student_id, date, time, status)
            VALUES (?, ?, ?, 'Present')
        """, (student_id, today, now_time))
        conn.commit()
        conn.close()
        return True, now_time
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Attendance already marked today."


def get_today_attendance():
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.roll_number, s.name, a.time, a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.student_id
        WHERE a.date = ?
        ORDER BY a.time
    """, (today,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_dashboard_stats():
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM attendance WHERE date = ?", (today,))
    present_today = cursor.fetchone()[0]

    conn.close()

    absent_today = max(total_students - present_today, 0)
    rate = round((present_today / total_students) * 100, 1) if total_students else 0

    return {
        "total_students": total_students,
        "present_today": present_today,
        "absent_today": absent_today,
        "attendance_rate": rate,
    }


def get_attendance_filtered(department=None, semester=None, date=None, status=None):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT s.roll_number, s.name, s.department, s.semester, a.date, a.time, a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.student_id
        WHERE 1=1
    """
    params = []

    if department and department != "All":
        query += " AND s.department = ?"
        params.append(department)
    if semester and semester != "All":
        query += " AND s.semester = ?"
        params.append(semester)
    if date:
        query += " AND a.date = ?"
        params.append(date)
    if status and status != "All":
        query += " AND a.status = ?"
        params.append(status)

    query += " ORDER BY a.date DESC, a.time DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_student_report():
    """Per-student totals: classes held, present count, absent count, %."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(DISTINCT date) FROM attendance")
    total_classes = cursor.fetchone()[0] or 0

    cursor.execute("""
        SELECT s.student_id, s.name, s.roll_number,
               COUNT(a.attendance_id) AS present_count
        FROM students s
        LEFT JOIN attendance a ON s.student_id = a.student_id
        GROUP BY s.student_id
        ORDER BY s.roll_number
    """)
    rows = cursor.fetchall()
    conn.close()

    report = []
    for _student_id, name, roll_number, present_count in rows:
        absent = max(total_classes - present_count, 0)
        pct = round((present_count / total_classes) * 100, 1) if total_classes else 0
        report.append({
            "name": name,
            "roll_number": roll_number,
            "total_classes": total_classes,
            "present": present_count,
            "absent": absent,
            "attendance_pct": pct,
        })
    return report


if __name__ == "__main__":
    create_database()
    print("AttendAI database created successfully!")
