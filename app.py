import streamlit as st
import sqlite3
import qrcode
import uuid
import os

DB_FILE = "database/attendai.db"
QR_FOLDER = "qrcodes"

os.makedirs(QR_FOLDER, exist_ok=True)


def register_student(name, roll_number, department, semester):
    qr_token = str(uuid.uuid4())

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO students
            (name, roll_number, department, semester, qr_token)
            VALUES (?, ?, ?, ?, ?)
        """, (name, roll_number, department, semester, qr_token))

        student_id = cursor.lastrowid
        conn.commit()

    except sqlite3.IntegrityError:
        conn.close()
        return None, "Roll number already exists."

    conn.close()

    qr_data = qr_token
    qr_image = qrcode.make(qr_data)

    qr_path = os.path.join(QR_FOLDER, f"{roll_number}.png")
    qr_image.save(qr_path)

    return qr_path, student_id


st.set_page_config(
    page_title="AttendAI",
    page_icon="📋",
    layout="centered"
)

st.title("AttendAI")
st.subheader("Student Registration")

name = st.text_input("Student Name")
roll_number = st.text_input("Roll Number")
department = st.text_input("Department")
semester = st.number_input(
    "Semester",
    min_value=1,
    max_value=8,
    step=1
)

if st.button("Register Student"):

    if not name or not roll_number or not department:
        st.warning("Please fill all fields.")

    else:
        qr_path, result = register_student(
            name,
            roll_number,
            department,
            semester
        )

        if qr_path is None:
            st.error(result)

        else:
            st.success("Student registered successfully!")

            st.write(f"Student ID: {result}")
            st.write(f"Roll Number: {roll_number}")

            st.image(
                qr_path,
                caption=f"QR Code - {roll_number}",
                width=250
            )