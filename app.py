import os
import sqlite3
import requests

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "students.db")

# Partner API URL
PARTNER_URL = os.environ.get(
    "PARTNER_API_URL",
    "https://gwynethjoylaudv1.onrender.com/api/students"
)

REQUEST_TIMEOUT = 20


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            name TEXT NOT NULL,
            program TEXT NOT NULL,
            year INTEGER NOT NULL,
            section TEXT NOT NULL,
            source TEXT DEFAULT 'Local'
        )
    """)

    columns = [
        row["name"]
        for row in conn.execute("PRAGMA table_info(students)").fetchall()
    ]

    if "source" not in columns:
        conn.execute(
            "ALTER TABLE students ADD COLUMN source TEXT DEFAULT 'Local'"
        )

    conn.commit()
    conn.close()


def validate_student(data):
    if not isinstance(data, dict):
        return None, "Invalid student data."

    required_fields = [
        "student_id",
        "name",
        "program",
        "year",
        "section"
    ]

    for field in required_fields:
        if data.get(field) is None or str(data[field]).strip() == "":
            return None, f"Missing required field: {field}"

    try:
        year = int(data["year"])

        if year < 1 or year > 10:
            return None, "Year must be between 1 and 10."

    except (ValueError, TypeError):
        return None, "Year must be a valid number."

    student = {
        "student_id": str(data["student_id"]).strip(),
        "name": str(data["name"]).strip(),
        "program": str(data["program"]).strip(),
        "year": year,
        "section": str(data["section"]).strip()
    }

    return student, None


def get_partner_students(data):
    """Accept common response formats from partner APIs."""

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in ["students", "data", "records", "results"]:
            if isinstance(data.get(key), list):
                return data[key]

    return None


def insert_student(student, source):
    """Insert a validated student record into the local database."""

    conn = get_db_connection()

    try:
        cursor = conn.execute(
            """
            INSERT INTO students
            (student_id, name, program, year, section, source)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                student["student_id"],
                student["name"],
                student["program"],
                student["year"],
                student["section"],
                source
            )
        )

        conn.commit()
        return cursor.lastrowid

    finally:
        conn.close()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api")
def api_home():
    return jsonify({
        "message": "Welcome to my first API"
    })


@app.route("/student")
def student():
    return jsonify({
        "student_id": "24-00145",
        "name": "Yvonne Mahilum",
        "program": "BSIT",
        "year": 3,
        "section": "B"
    })


@app.route("/hello")
def hello():
    name = request.args.get("name", "Student")

    return jsonify({
        "message": f"Hello, {name}!"
    })


@app.route("/course")
def course():
    return jsonify({
        "course": "Bachelor of Science in Information Technology",
        "program": "BSIT",
        "description": "A program focused on information technology."
    })


@app.route("/skills")
def skills():
    return jsonify({
        "skills": [
            "HTML",
            "CSS",
            "JavaScript",
            "Python",
            "Flask",
            "SQLite"
        ]
    })


# GET ALL STUDENTS
@app.route("/students", methods=["GET"])
@app.route("/api/students", methods=["GET"])
def get_students():
    conn = get_db_connection()

    try:
        students = conn.execute(
            "SELECT * FROM students ORDER BY id DESC"
        ).fetchall()

        return jsonify([dict(student) for student in students])

    finally:
        conn.close()


# INTEGRATION DASHBOARD: LOCAL RECORDS
@app.route("/api/integration/local", methods=["GET"])
def get_local_records():
    conn = get_db_connection()

    try:
        students = conn.execute(
            """
            SELECT * FROM students
            WHERE LOWER(COALESCE(source, 'Local')) = 'local'
            ORDER BY id DESC
            """
        ).fetchall()

        return jsonify([dict(student) for student in students])

    finally:
        conn.close()


# INTEGRATION DASHBOARD: IMPORTED RECORDS
@app.route("/api/integration/imported", methods=["GET"])
def get_imported_records():
    conn = get_db_connection()

    try:
        students = conn.execute(
            """
            SELECT * FROM students
            WHERE LOWER(COALESCE(source, 'Local')) != 'local'
            ORDER BY id DESC
            """
        ).fetchall()

        return jsonify([dict(student) for student in students])

    finally:
        conn.close()


# GET STUDENTS BY SECTION
@app.route("/students/section/<section_name>")
def get_students_by_section(section_name):
    conn = get_db_connection()

    try:
        students = conn.execute(
            """
            SELECT * FROM students
            WHERE section = ?
            ORDER BY id DESC
            """,
            (section_name,)
        ).fetchall()

        return jsonify([dict(student) for student in students])

    finally:
        conn.close()


# GET ONE STUDENT
@app.route("/students/<int:id>", methods=["GET"])
@app.route("/api/students/<int:id>", methods=["GET"])
def get_student(id):
    conn = get_db_connection()

    try:
        student = conn.execute(
            "SELECT * FROM students WHERE id = ?",
            (id,)
        ).fetchone()

        if student is None:
            return jsonify({"error": "Student not found"}), 404

        return jsonify(dict(student))

    finally:
        conn.close()


# RETRIEVE PARTNER RECORDS
@app.route("/partner-records", methods=["GET"])
def partner_records():
    try:
        response = requests.get(
            PARTNER_URL,
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        try:
            partner_data = response.json()
        except ValueError:
            return jsonify({
                "error": "Partner API returned invalid JSON."
            }), 502

        students = get_partner_students(partner_data)

        if students is None:
            return jsonify({
                "error": "Partner API response does not contain a student list.",
                "partner_response": partner_data
            }), 502

        return jsonify({
            "message": "Partner records retrieved successfully.",
            "students": students
        })

    except requests.Timeout:
        return jsonify({
            "error": "The partner API request timed out."
        }), 504

    except requests.RequestException as e:
        return jsonify({
            "error": "Unable to retrieve partner records.",
            "details": str(e)
        }), 502


# ADD STUDENT / RECEIVE EXTERNAL API RECORD
@app.route("/api/students", methods=["POST"])
def add_student():
    data = request.get_json(silent=True) or {}

    student, error = validate_student(data)

    if error:
        return jsonify({"error": error}), 400

    source = data.get("source", "External API")

    if not isinstance(source, str) or not source.strip():
        source = "External API"

    source = source.strip()

    try:
        new_id = insert_student(student, source)

        return jsonify({
            "message": "Student record received successfully.",
            "id": new_id,
            "student": student,
            "source": source
        }), 201

    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500


# IMPORT A SELECTED PARTNER RECORD
@app.route("/import-student", methods=["POST"])
def import_student():
    data = request.get_json(silent=True) or {}

    student, error = validate_student(data)

    if error:
        return jsonify({"error": error}), 400

    conn = get_db_connection()

    try:
        existing = conn.execute(
            """
            SELECT id FROM students
            WHERE student_id = ?
            LIMIT 1
            """,
            (student["student_id"],)
        ).fetchone()

        if existing:
            return jsonify({
                "error": "This student ID already exists in your database.",
                "existing_id": existing["id"]
            }), 409

        cursor = conn.execute(
            """
            INSERT INTO students
            (student_id, name, program, year, section, source)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                student["student_id"],
                student["name"],
                student["program"],
                student["year"],
                student["section"],
                "Classmate API"
            )
        )

        conn.commit()

        return jsonify({
            "message": "Partner record successfully imported.",
            "id": cursor.lastrowid,
            "student": student,
            "source": "Classmate API"
        }), 201

    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()


# SEND A PRACTICE RECORD TO PARTNER
@app.route("/send-practice-record", methods=["POST"])
def send_practice_record():
    record = {
        "student_id": "EXT-001",
        "name": "Sample Exchange Record",
        "program": "BSIT",
        "year": 1,
        "section": "A",
        "source": "Partner API"
    }

    try:
        response = requests.post(
            PARTNER_URL,
            json=record,
            timeout=REQUEST_TIMEOUT
        )

        try:
            partner_response = response.json()
        except ValueError:
            partner_response = response.text

        result = {
            "message": (
                "Partner API accepted the request."
                if response.ok
                else "Partner API did not accept the record."
            ),
            "status_code": response.status_code,
            "sent_record": record,
            "partner_response": partner_response
        }

        return jsonify(result), 200 if response.ok else 502

    except requests.Timeout:
        return jsonify({
            "error": "Sending the record timed out."
        }), 504

    except requests.RequestException as e:
        return jsonify({
            "error": "Could not send the practice record to the partner API.",
            "details": str(e)
        }), 502


# UPDATE STUDENT
@app.route("/api/students/<int:id>", methods=["PUT"])
def update_student(id):
    data = request.get_json(silent=True) or {}

    student, error = validate_student(data)

    if error:
        return jsonify({"error": error}), 400

    conn = get_db_connection()

    try:
        cursor = conn.execute(
            """
            UPDATE students
            SET student_id = ?,
                name = ?,
                program = ?,
                year = ?,
                section = ?
            WHERE id = ?
            """,
            (
                student["student_id"],
                student["name"],
                student["program"],
                student["year"],
                student["section"],
                id
            )
        )

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Student not found"}), 404

        return jsonify({
            "message": "Student updated successfully."
        })

    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()


# DELETE STUDENT
@app.route("/api/students/<int:id>", methods=["DELETE"])
def delete_student(id):
    conn = get_db_connection()

    try:
        cursor = conn.execute(
            "DELETE FROM students WHERE id = ?",
            (id,)
        )

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Student not found"}), 404

        return jsonify({
            "message": "Student deleted successfully."
        })

    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()


# INITIALIZE DATABASE WHEN THE APP STARTS
initialize_database()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )