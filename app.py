
import sqlite3
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)


def get_db_connection():
    conn = sqlite3.connect('students.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def home():
    return render_template('index.html')


# Get one student by student number
@app.route('/student')
def get_student():
    conn = get_db_connection()

    student = conn.execute(
        'SELECT * FROM students WHERE student_id = ?',
        ('2026-00123',)
    ).fetchone()

    conn.close()

    if student is None:
        return jsonify({'error': 'Student not found'}), 404

    return jsonify(dict(student))


# Get all students
@app.route('/students')
def get_students():
    conn = get_db_connection()

    students = conn.execute(
        'SELECT * FROM students'
    ).fetchall()

    conn.close()

    return jsonify([dict(student) for student in students])


# Get a student by database ID
@app.route('/students/<int:id>')
def get_student_by_id(id):
    conn = get_db_connection()

    student = conn.execute(
        'SELECT * FROM students WHERE id = ?',
        (id,)
    ).fetchone()

    conn.close()

    if student is None:
        return jsonify({'error': 'Student not found'}), 404

    return jsonify(dict(student))


# Hello endpoint
@app.route('/hello')
def say_hello():
    name = request.args.get('name', 'Student')

    return jsonify({
        'message': f'Hello, {name}!'
    })


# Skills endpoint
@app.route('/skills')
def get_skills():
    return jsonify({
        'skills': [
            'Python',
            'Flask',
            'HTML',
            'CSS',
            'JavaScript',
            'Database Management'
        ]
    })


if __name__ == '__main__':
    app.run(debug=True)
