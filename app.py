
import os
import sqlite3
import time
import requests

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATABASE = "students.db"

PARTNER_URL = "https://gwynethjoylaudv1.onrender.com/api/students"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api")
def api():
    return "Welcome to my first API"


@app.route("/student")
def get_student():
    return jsonify({
        "student_id": "24-00145",
        "name": "Yvonne Mahilum",
        "program": "BSIT",
        "year": 3,
        "section": "B"
    })


@app.route("/students", methods=["GET"])
@app.route("/api/students", methods=["GET"])
def get_students():
    conn = get_db_connection()

    try:
        students = conn.execute(
            "SELECT * FROM students"
        ).fetchall()

        return jsonify([dict(student) for student in students])

    except sqlite3.OperationalError as error:
        return jsonify({
            "error": "Database table not found. Please run init_db.py first.",
            "details": str(error)
        }), 500

    finally:
        conn.close()


@app.route("/students/section/<section_name>")
def get_students_by_section(section_name):
    conn = get_db_connection()

    try:
        students = conn.execute(
            "SELECT * FROM students WHERE section = ?",
            (section_name.upper(),)
        ).fetchall()

        return jsonify([dict(student) for student in students])

    finally:
        conn.close()


@app.route("/students/<int:id>")
@app.route("/api/students/<int:id>", methods=["GET"])
def get_student_by_id(id):
    conn = get_db_connection()

    try:
        student = conn.execute(
            "SELECT * FROM students WHERE id = ?",
            (id,)
        ).fetchone()

    finally:
        conn.close()

    if student is None:
        return jsonify({"error": "Student not found"}), 404

    return jsonify(dict(student))


@app.route("/hello")
def say_hello():
    name = request.args.get("name", "Student")

    return jsonify({
        "message": f"Hello, {name}!"
    })


@app.route("/course")
def get_course():
    return jsonify({
        "course": "Bachelor of Science in Information Technology",
        "code": "BSIT",
        "program": "BSIT",
        "year": 3,
        "section": "B",
        "description": "Bachelor of Science in Information Technology"
    })


@app.route("/skills")
def get_skills():
    return jsonify({
        "skills": [
            "Python",
            "Flask",
            "HTML",
            "CSS",
            "JavaScript",
            "Database Management"
        ]
    })


# ==========================================
# CLASSMATE API PROXY
# ==========================================

@app.route("/partner-records", methods=["GET"])
def partner_records():

    last_error = None

    # Retry the connection in case Render is waking up.
    for attempt in range(1, 3):

        try:
            response = requests.get(
                PARTNER_URL,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "Student-API-Interface"
                },
                timeout=(10, 60)
            )

            response.raise_for_status()

            try:
                partner_data = response.json()

            except ValueError:
                return jsonify({
                    "error": "The partner server did not return valid JSON."
                }), 502

            # Return the partner's original JSON response.
            return jsonify(partner_data)

        except requests.RequestException as error:

            last_error = str(error)

            print(
                f"Partner API attempt {attempt} failed: {last_error}"
            )

            if attempt < 2:
                time.sleep(3)

    return jsonify({
        "error": "Unable to retrieve classmate records.",
        "details": last_error,
        "partner_url": PARTNER_URL
    }), 502


# ==========================================
# ADD STUDENT
# ==========================================

@app.route("/api/students", methods=["POST"])
def add_student():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Valid JSON data is required"
        }), 400

    required = [
        "student_id",
        "name",
        "program",
        "year",
        "section"
    ]

    if any(field not in data for field in required):
        return jsonify({
            "error": "All student fields are required",
            "required_fields": required
        }), 400

    if any(
        not str(data[field]).strip()
        for field in ["student_id", "name", "program", "section"]
    ):
        return jsonify({
            "error": "Student fields cannot be empty"
        }), 400

    try:
        year = int(data["year"])

        if year < 1 or year > 10:
            raise ValueError

    except (TypeError, ValueError):
        return jsonify({
            "error": "Year must be a number from 1 to 10"
        }), 400

    conn = get_db_connection()

    try:
        cursor = conn.execute(
            """
            INSERT INTO students
                (student_id, name, program, year, section)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                str(data["student_id"]).strip(),
                str(data["name"]).strip(),
                str(data["program"]).strip(),
                year,
                str(data["section"]).strip().upper()
            )
        )

        conn.commit()
        new_id = cursor.lastrowid

    except sqlite3.IntegrityError as error:
        return jsonify({
            "error": f"Could not add student: {error}"
        }), 400

    finally:
        conn.close()

    return jsonify({
        "message": "Student added successfully",
        "id": new_id
    }), 201


# ==========================================
# UPDATE STUDENT
# ==========================================

@app.route("/api/students/<int:id>", methods=["PUT"])
def update_student(id):

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Valid JSON data is required"
        }), 400

    required = [
        "student_id",
        "name",
        "program",
        "year",
        "section"
    ]

    if any(field not in data for field in required):
        return jsonify({
            "error": "All student fields are required",
            "required_fields": required
        }), 400

    if any(
        not str(data[field]).strip()
        for field in ["student_id", "name", "program", "section"]
    ):
        return jsonify({
            "error": "Student fields cannot be empty"
        }), 400

    try:
        year = int(data["year"])

        if year < 1 or year > 10:
            raise ValueError

    except (TypeError, ValueError):
        return jsonify({
            "error": "Year must be a number from 1 to 10"
        }), 400

    conn = get_db_connection()

    try:
        existing = conn.execute(
            "SELECT id FROM students WHERE id = ?",
            (id,)
        ).fetchone()

        if existing is None:
            return jsonify({
                "error": "Student not found"
            }), 404

        conn.execute(
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
                str(data["student_id"]).strip(),
                str(data["name"]).strip(),
                str(data["program"]).strip(),
                year,
                str(data["section"]).strip().upper(),
                id
            )
        )

        conn.commit()

    except sqlite3.IntegrityError as error:
        return jsonify({
            "error": f"Could not update student: {error}"
        }), 400

    finally:
        conn.close()

    return jsonify({
        "message": "Student updated successfully"
    })


# ==========================================
# DELETE STUDENT
# ==========================================

@app.route("/api/students/<int:id>", methods=["DELETE"])
def delete_student(id):

    conn = get_db_connection()

    try:
        cursor = conn.execute(
            "DELETE FROM students WHERE id = ?",
            (id,)
        )

        if cursor.rowcount == 0:
            return jsonify({
                "error": "Student not found"
            }), 404

        conn.commit()

    finally:
        conn.close()

    return jsonify({
        "message": "Student deleted successfully"
    })


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )
