# 📋 AttendAI — QR-Based Attendance System

AttendAI is a lightweight, QR-code-based attendance system built with
**Streamlit** and **SQLite**. Students register once and get a unique QR
code; a teacher scans that code with a webcam to mark attendance, and the
app tracks stats, reports, and CSV exports automatically.

## Features (V1)

- **Student Registration** — name, roll number, department, semester,
  with a unique auto-generated QR code per student.
- **Duplicate protection** — roll numbers are unique at the database level.
- **Student directory** — search, filter by department/semester, view QR
  codes, delete students.
- **Attendance via QR scan** — uses the browser camera (`st.camera_input`)
  and OpenCV's built-in QR detector, so no extra system libraries are
  needed and it works the same locally and on Streamlit Cloud.
- **Dashboard** — total students, present/absent today, attendance rate.
- **Reports** — per-student attendance % across all classes held, plus a
  filterable attendance log (department, semester, date, status).
- **CSV export** — download any report or filtered log for Excel.

## Project Structure

```
AttendAI/
│
├── app.py              # Streamlit app (all pages/navigation)
├── database.py          # SQLite schema + all data access functions
├── requirements.txt
├── .gitignore
│
├── database/             # created at runtime, holds attendai.db (git-ignored)
└── qrcodes/               # created at runtime, holds generated QR images (git-ignored)
```

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/Fayaz-unar/AttendAI.git
cd AttendAI

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

## How attendance scanning works

Rather than a continuous OpenCV video loop (which doesn't work well once
deployed to the cloud, and needs extra permissions/drivers locally),
AttendAI uses Streamlit's built-in `st.camera_input`: the user takes a
single snapshot of the student's QR code, and OpenCV's `QRCodeDetector`
decodes it from that image. This keeps the app deployable as-is to
Streamlit Community Cloud with zero extra configuration.

## Roadmap

- [ ] Face recognition as a secondary/backup check
- [ ] Teacher login / multi-class support
- [ ] Charts (attendance trend over time) on the dashboard
- [ ] Bulk student import via CSV

## Deployment (Streamlit Community Cloud)

1. Push this repo to GitHub (already done — see `.gitignore` for what's
   excluded, notably the venv and the SQLite database).
2. Go to [share.streamlit.io](https://share.streamlit.io), connect your
   GitHub account, and pick this repo + `app.py` as the entry point.
3. Streamlit Cloud installs everything in `requirements.txt`
   automatically and gives you a public URL.

## Tech Stack

- [Streamlit](https://streamlit.io) — UI & app framework
- [SQLite](https://www.sqlite.org/) — local database
- [qrcode](https://pypi.org/project/qrcode/) — QR code generation
- [OpenCV](https://opencv.org/) — QR code decoding from camera snapshots
- [pandas](https://pandas.pydata.org/) — tables & CSV export
