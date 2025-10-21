from flask import Flask, render_template, request, redirect, url_for, session
import PyPDF2
import docx
import os
import csv
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'placement_secret_key'

# ---------- Resume Upload ----------
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# ---------- Resume Parser ----------
def extract_text_from_file(filepath):
    text = ""
    if filepath.endswith(".pdf"):
        with open(filepath, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text()
    elif filepath.endswith(".docx"):
        doc = docx.Document(filepath)
        for para in doc.paragraphs:
            text += para.text + " "
    return text.lower()


def calculate_resume_score(text):
    skills = [
        "python", "java", "c", "html", "css", "javascript",
        "node", "express", "flask", "django", "mongodb",
        "mysql", "data analysis", "machine learning", "git", "github"
    ]
    matched = [skill for skill in skills if skill in text]
    score = int((len(matched) / len(skills)) * 100)
    return score, matched


# ---------- Database Setup ----------
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    # User Table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  email TEXT UNIQUE,
                  password TEXT)''')
    # Aptitude Table
    c.execute('''CREATE TABLE IF NOT EXISTS aptitude
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  score INTEGER,
                  test_date TEXT)''')
    # Certification Table
    c.execute('''CREATE TABLE IF NOT EXISTS certifications
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  title TEXT,
                  date TEXT)''')
    # Resume Table
    c.execute('''CREATE TABLE IF NOT EXISTS resume_data
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  filename TEXT,
                  score INTEGER)''')
    conn.commit()
    conn.close()


# ---------- Helper Function ----------
def calculate_readiness(user_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT AVG(score) FROM aptitude WHERE user_id=?", (user_id,))
    aptitude_score = c.fetchone()[0] or 0

    c.execute("SELECT COUNT(*) FROM certifications WHERE user_id=?", (user_id,))
    cert_count = c.fetchone()[0] or 0

    c.execute("SELECT AVG(score) FROM resume_data WHERE user_id=?", (user_id,))
    resume_score = c.fetchone()[0] or 0

    total = (resume_score * 0.4) + (aptitude_score * 0.4) + (cert_count * 10)

    # Smart feedback
    if total >= 85:
        feedback = "Excellent readiness! You’re well-prepared for placements."
    elif total >= 65:
        feedback = "Good progress! Focus on more certifications and skill-building."
    elif total >= 45:
        feedback = "Average readiness. Improve your aptitude and resume quality."
    else:
        feedback = "Low readiness. Strengthen your basics and attempt more mock tests."

    conn.close()
    return round(total, 2), feedback



# ---------- Routes ----------
@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
            conn.commit()
            return redirect(url_for('login'))
        except:
            return "User already exists!"
        finally:
            conn.close()
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = c.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials!"
    return render_template('login.html')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT score, test_date FROM aptitude WHERE user_id=?", (user_id,))
    aptitude_data = c.fetchall()

    c.execute("SELECT title, date FROM certifications WHERE user_id=?", (user_id,))
    cert_data = c.fetchall()

    c.execute("SELECT score FROM resume_data WHERE user_id=?", (user_id,))
    resume_data = c.fetchall()

    conn.close()

    readiness, feedback = calculate_readiness(user_id)

    return render_template('dashboard.html',
                           user=session['user_name'],
                           aptitude_data=aptitude_data,
                           cert_data=cert_data,
                           resume_data=resume_data,
                           readiness=readiness,
                           feedback=feedback)


@app.route('/add_aptitude', methods=['POST'])
def add_aptitude():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    score = int(request.form['score'])
    date = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO aptitude (user_id, score, test_date) VALUES (?, ?, ?)", (session['user_id'], score, date))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))


@app.route('/add_certification', methods=['POST'])
def add_certification():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    title = request.form['title']
    date = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO certifications (user_id, title, date) VALUES (?, ?, ?)", (session['user_id'], title, date))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))


@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    file = request.files['resume']
    if file.filename == "":
        return "No file selected"

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    text = extract_text_from_file(filepath)
    score, matched_skills = calculate_resume_score(text)

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO resume_data (user_id, filename, score) VALUES (?, ?, ?)",
              (session['user_id'], file.filename, score))
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))


# ---------- Reset Database Route ----------
@app.route('/reset_database')
def reset_database():
    try:
        if os.path.exists("database.db"):
            os.remove("database.db")
        init_db()
        return "✅ Database has been reset successfully. Restart the app and re-register users."
    except Exception as e:
        return f"❌ Error resetting database: {e}"


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ---------- Advanced Admin Routes ----------

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email == "admin@tracker.com" and password == "admin123":
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return "Invalid admin credentials!"
    return render_template('admin_login.html')


@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id, name, email FROM users")
    users = c.fetchall()

    all_data = []
    for user in users:
        user_id, name, email = user
        c.execute("SELECT AVG(score) FROM aptitude WHERE user_id=?", (user_id,))
        aptitude = c.fetchone()[0] or 0
        c.execute("SELECT COUNT(*) FROM certifications WHERE user_id=?", (user_id,))
        certs = c.fetchone()[0] or 0
        c.execute("SELECT AVG(score) FROM resume_data WHERE user_id=?", (user_id,))
        resume = c.fetchone()[0] or 0
        total = (resume * 0.4) + (aptitude * 0.4) + (certs * 10)
        all_data.append((name, email, round(resume, 1), round(aptitude, 1), certs, round(total, 1)))

    conn.close()

    # Sort and get top performers
    top_performers = sorted(all_data, key=lambda x: x[5], reverse=True)[:3]
    return render_template('admin_dashboard.html', all_data=all_data, top_performers=top_performers)


@app.route('/export_csv')
def export_csv():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id, name, email FROM users")
    users = c.fetchall()

    rows = []
    for user in users:
        user_id, name, email = user
        c.execute("SELECT AVG(score) FROM aptitude WHERE user_id=?", (user_id,))
        aptitude = c.fetchone()[0] or 0
        c.execute("SELECT COUNT(*) FROM certifications WHERE user_id=?", (user_id,))
        certs = c.fetchone()[0] or 0
        c.execute("SELECT AVG(score) FROM resume_data WHERE user_id=?", (user_id,))
        resume = c.fetchone()[0] or 0
        total = (resume * 0.4) + (aptitude * 0.4) + (certs * 10)
        rows.append((name, email, round(resume, 1), round(aptitude, 1), certs, round(total, 1)))

    conn.close()

    # Write CSV
    import csv
    filename = "student_readiness_report.csv"
    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Name", "Email", "Resume Score", "Aptitude Score", "Certifications", "Total Readiness"])
        writer.writerows(rows)

    return f"✅ CSV exported successfully as '{filename}' in the project folder."


@app.route('/admin_logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
