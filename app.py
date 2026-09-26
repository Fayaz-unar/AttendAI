import streamlit as st
import pandas as pd
import numpy as np
import cv2
import plotly.express as px
from streamlit_option_menu import option_menu

import database as db

st.set_page_config(page_title="AttendAI", page_icon="📋", layout="wide")
db.create_database()

PRIMARY = "#5b3fd6"
TEAL = "#17c3b2"
ORANGE = "#f4802b"
GREEN = "#27ae60"

# ---------------------------------------------------------------------------
# Global theme (cards, sidebar, section panels)
# ---------------------------------------------------------------------------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
}}

.stApp {{
    background-color: #f4f6fb;
}}

section[data-testid="stSidebar"] {{
    background-color: #ffffff;
    border-right: 1px solid #eef0f5;
}}

.block-container {{
    padding-top: 2rem;
    padding-bottom: 3rem;
}}

h1, h2, h3 {{
    color: #1f2333;
}}

/* metric cards */
.metric-card {{
    border-radius: 16px;
    padding: 20px 22px;
    color: white;
    min-height: 100px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 8px 20px rgba(0,0,0,0.08);
    margin-bottom: 8px;
}}
.metric-label {{
    font-size: 13px;
    opacity: 0.9;
    font-weight: 500;
}}
.metric-value {{
    font-size: 28px;
    font-weight: 700;
    margin-top: 4px;
}}
.metric-icon {{
    font-size: 26px;
    background: rgba(255,255,255,0.18);
    border-radius: 12px;
    width: 46px;
    height: 46px;
    display: flex;
    align-items: center;
    justify-content: center;
}}

/* section panels */
.section-card {{
    background: white;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.05);
    margin-bottom: 22px;
}}
.section-card h3 {{
    margin-top: 0;
}}

div[data-testid="stForm"] {{
    background: white;
    border-radius: 16px;
    padding: 22px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.05);
    border: none;
}}
</style>
""", unsafe_allow_html=True)


def metric_card(label, value, color, icon):
    st.markdown(f"""
        <div class="metric-card" style="background:{color};">
            <div>
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
            </div>
            <div class="metric-icon">{icon}</div>
        </div>
    """, unsafe_allow_html=True)


def section_start(title=None):
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    if title:
        st.subheader(title)


def section_end():
    st.markdown('</div>', unsafe_allow_html=True)


def decode_qr_from_image(image_array):
    detector = cv2.QRCodeDetector()
    data, _points, _straight_qr = detector.detectAndDecode(image_array)
    return data if data else None


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 📋 AttendAI")
    st.caption("AI-Based Attendance System")
    st.write("")
    page = option_menu(
        menu_title=None,
        options=["Dashboard", "Register Student", "Students", "Attendance", "Reports"],
        icons=["speedometer2", "person-plus", "people", "camera", "bar-chart-line"],
        default_index=0,
        styles={
            "container": {"padding": "0", "background-color": "transparent"},
            "icon": {"color": PRIMARY, "font-size": "16px"},
            "nav-link": {
                "font-size": "14px",
                "text-align": "left",
                "margin": "4px 0",
                "border-radius": "10px",
                "padding": "10px 14px",
            },
            "nav-link-selected": {"background-color": PRIMARY, "color": "white"},
        },
    )

# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
if page == "Dashboard":
    st.title("Dashboard")

    stats = db.get_dashboard_stats()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Total Students", stats["total_students"], TEAL, "🎓")
    with c2:
        metric_card("Departments", len(db.get_departments()), PRIMARY, "🏢")
    with c3:
        metric_card("Absent Today", stats["absent_today"], ORANGE, "🚫")
    with c4:
        metric_card("Attendance Rate", f"{stats['attendance_rate']}%", GREEN, "📈")

    st.write("")
    col1, col2 = st.columns(2)

    with col1:
        section_start("Students by Department")
        dist = db.get_department_distribution()
        if dist:
            df = pd.DataFrame(dist, columns=["Department", "Count"])
            fig = px.pie(
                df, names="Department", values="Count", hole=0.65,
                color_discrete_sequence=["#4a6cf7", "#e84393", "#fdcb6e", "#00b894", "#a55eea"],
            )
            fig.update_traces(textinfo="percent", textfont_size=12)
            fig.add_annotation(
                text=f"<b>{stats['total_students']}</b><br>Students",
                showarrow=False, font=dict(size=14, color="#1f2333"),
            )
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=320,
                               legend=dict(orientation="h", yanchor="bottom", y=-0.2))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Register students to see this chart.")
        section_end()

    with col2:
        section_start("Attendance — Last 7 Days")
        trend = db.get_weekly_trend()
        df = pd.DataFrame(trend, columns=["Day", "Present"])
        fig = px.bar(df, x="Day", y="Present", color_discrete_sequence=[PRIMARY])
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=320)
        st.plotly_chart(fig, use_container_width=True)
        section_end()

    section_start("Today's Attendance")
    rows = db.get_today_attendance()
    if rows:
        df = pd.DataFrame(rows, columns=["Roll No.", "Name", "Time", "Status"])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No attendance marked yet today.")
    section_end()


# ---------------------------------------------------------------------------
# Register Student
# ---------------------------------------------------------------------------
elif page == "Register Student":
    st.title("Student Registration")

    with st.form("register_form", clear_on_submit=True):
        st.subheader("New Student Details")
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Student Name")
            department = st.text_input("Department")
        with c2:
            roll_number = st.text_input("Roll Number")
            semester = st.number_input("Semester", min_value=1, max_value=8, step=1)
        submitted = st.form_submit_button("Register Student", type="primary")

    if submitted:
        if not name or not roll_number or not department:
            st.warning("Please fill all fields.")
        else:
            qr_path, result = db.register_student(name, roll_number, department, semester)
            if qr_path is None:
                st.error(result)
            else:
                section_start("Registration Successful")
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.write(f"**Student ID:** {result}")
                    st.write(f"**Name:** {name}")
                    st.write(f"**Roll Number:** {roll_number}")
                    st.write(f"**Department:** {department}")
                    st.write(f"**Semester:** {semester}")
                with c2:
                    st.image(qr_path, caption=f"QR Code - {roll_number}", width=200)
                section_end()


# ---------------------------------------------------------------------------
# Students
# ---------------------------------------------------------------------------
elif page == "Students":
    st.title("Registered Students")

    section_start("Search & Filter")
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search = st.text_input("Search by name or roll number")
    with col2:
        departments = ["All"] + db.get_departments()
        department = st.selectbox("Department", departments)
    with col3:
        semester = st.selectbox("Semester", ["All"] + list(range(1, 9)))
    section_end()

    students = db.get_all_students(search=search, department=department, semester=semester)

    section_start("Student Directory")
    if students:
        df = pd.DataFrame(
            students,
            columns=["Student ID", "Name", "Roll Number", "Department", "Semester", "QR Token"],
        )
        st.dataframe(df.drop(columns=["QR Token"]), use_container_width=True, hide_index=True)
    else:
        st.info("No students found. Register one first.")
    section_end()

    if students:
        section_start("Manage a Student")
        options = {f"{s[2]} - {s[1]}": s for s in students}
        choice = st.selectbox("Select student", list(options.keys()))
        selected = options[choice]

        c1, c2 = st.columns(2)
        with c1:
            if st.button("View QR Code"):
                st.image(f"qrcodes/{selected[2]}.png", caption=selected[2], width=200)
        with c2:
            if st.button("Delete Student", type="secondary"):
                db.delete_student(selected[0])
                st.success(f"Deleted {selected[1]} ({selected[2]}).")
                st.rerun()
        section_end()


# ---------------------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------------------
elif page == "Attendance":
    st.title("Mark Attendance")

    tab1, tab2 = st.tabs(["📷 Scan QR Code", "⌨️ Enter Roll Number"])

    with tab1:
        section_start()
        st.caption("Show the student's QR code to the camera and take a snapshot.")
        img_file = st.camera_input("Scan QR Code")

        if img_file is not None:
            bytes_data = np.frombuffer(img_file.getvalue(), np.uint8)
            image = cv2.imdecode(bytes_data, cv2.IMREAD_COLOR)
            qr_token = decode_qr_from_image(image)

            if qr_token:
                student = db.get_student_by_token(qr_token)
                if student:
                    student_id, name, roll_number, _dept, _sem = student
                    success, result = db.mark_attendance(student_id)
                    if success:
                        st.success(f"Attendance marked for {name} ({roll_number}) at {result}")
                    else:
                        st.warning(f"{name} ({roll_number}): {result}")
                else:
                    st.error("QR code not recognized. Student not found.")
            else:
                st.error("No QR code detected. Try again with better lighting or focus.")
        section_end()

    with tab2:
        with st.form("roll_attendance_form", clear_on_submit=True):
            st.caption("Type the student's roll number and mark them present manually.")
            roll_number_input = st.text_input("Roll Number")
            submitted = st.form_submit_button("Mark Present", type="primary")

        if submitted:
            if not roll_number_input:
                st.warning("Please enter a roll number.")
            else:
                student = db.get_student_by_roll(roll_number_input)
                if student:
                    student_id, name, roll_no, _dept, _sem = student
                    success, result = db.mark_attendance(student_id)
                    if success:
                        st.success(f"Attendance marked for {name} ({roll_no}) at {result}")
                    else:
                        st.warning(f"{name} ({roll_no}): {result}")
                else:
                    st.error("No student found with that roll number.")

    st.write("")
    section_start("Today's Attendance")
    rows = db.get_today_attendance()
    if rows:
        df = pd.DataFrame(rows, columns=["Roll No.", "Name", "Time", "Status"])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No attendance marked yet today.")
    section_end()


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------
elif page == "Reports":
    st.title("Attendance Reports")

    tab1, tab2 = st.tabs(["Per-Student Report", "Filtered Attendance Log"])

    with tab1:
        section_start()
        report = db.get_student_report()
        if report:
            df = pd.DataFrame(report)
            df.columns = ["Name", "Roll Number", "Total Classes", "Present", "Absent", "Attendance %"]
            st.dataframe(df, use_container_width=True, hide_index=True)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download Report CSV", csv, "attendance_report.csv", "text/csv")
        else:
            st.info("No data yet. Register students and mark attendance first.")
        section_end()

    with tab2:
        section_start("Filters")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            departments = ["All"] + db.get_departments()
            department = st.selectbox("Department", departments, key="f_dept")
        with col2:
            semester = st.selectbox("Semester", ["All"] + list(range(1, 9)), key="f_sem")
        with col3:
            date = st.date_input("Date", value=None)
            date_str = date.strftime("%Y-%m-%d") if date else None
        with col4:
            status = st.selectbox("Status", ["All", "Present", "Absent"], key="f_status")
        section_end()

        section_start("Results")
        rows = db.get_attendance_filtered(
            department, semester, date_str, status if status != "All" else None
        )
        if rows:
            df = pd.DataFrame(
                rows,
                columns=["Roll Number", "Name", "Department", "Semester", "Date", "Time", "Status"],
            )
            st.dataframe(df, use_container_width=True, hide_index=True)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download Filtered CSV", csv, "attendance.csv", "text/csv")
        else:
            st.info("No records match these filters.")
        section_end()
