# 📋 AttendAI — QR-Based Attendance System

AttendAI is a QR-code-based student attendance system with a clean,
dashboard-style interface built in Streamlit.

## Features & Options

### Dashboard
- Total Students, Departments, Absent Today, and Attendance Rate summary cards
- Students-by-department donut chart
- Attendance trend for the last 7 days (bar chart)
- Today's attendance table

### Register Student
- Register a student with name, roll number, department, and semester
- Automatically generates and displays a unique QR code per student
- Blocks duplicate roll numbers

### Students
- Search students by name or roll number
- Filter by department and semester
- View a student's QR code
- Delete a student

### Attendance
- **Scan QR Code** — take a camera snapshot of a student's QR code to mark them present
- **Enter Roll Number** — manually type a roll number to mark attendance without scanning
- Live "Today's Attendance" table on the same page

### Reports
- **Per-Student Report** — total classes, present, absent, and attendance % for every student
- **Filtered Attendance Log** — filter records by department, semester, date, and status
- **CSV Export** — download either report for Excel

- https://attendai-fayazali.streamlit.app/
