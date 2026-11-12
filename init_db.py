import sqlite3

# Connect to the database (creates students.db if it doesn't exist)
conn = sqlite3.connect("students.db")
cursor = conn.cursor()

# Create the students table
cursor.execute("""
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

# Add source column if the table already exists without it
columns = [column[1] for column in cursor.execute(
    "PRAGMA table_info(students)"
).fetchall()]

if "source" not in columns:
    cursor.execute("""
        ALTER TABLE students
        ADD COLUMN source TEXT DEFAULT 'Local'
    """)

# Clear existing student records
cursor.execute("DELETE FROM students")

# Student data
students = [
    ("24-00123", "Yvonne Mahilum", "BSIT", 3, "B", "Local"),
    ("24-00146", "Gwyneth Joy Laud", "BSIT", 3, "B", "Local"),
    ("24-0087", "Kc Jane Marie Ladoing", "BSIT", 3, "B", "Local"),
    ("24-0087", "Yvette Mahilum", "BSIT", 1, "C", "Local"),
    ("24-0247", "Clark Vincent Labrador", "BSIT", 3, "B", "Local")
]

# Insert student records
cursor.executemany("""
INSERT INTO students (student_id, name, program, year, section, source)
VALUES (?, ?, ?, ?, ?, ?)
""", students)

# Save changes and close the database
conn.commit()
conn.close()

print("Database created successfully.")