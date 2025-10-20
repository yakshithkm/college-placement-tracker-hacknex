from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'placement_secret_key'

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
    conn.commit()
    conn.close()


# ---------- Helper Function ----------
def calculate_readiness(user_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Get aptitude score (average)
    c.execute("SELECT AVG(score) FROM aptitude WHERE user_id=?", (user_id,))
    aptitude_score = c.fetchone()[0] or 0

    # Count certifications
    c.execute("SELECT COUNT(*) FROM certifications WHERE user_id=?", (user_id,))
    cert_count = c.fetchone()[0] or 0

    resume_score = 75  # Placeholder for now

    # Weighted average
    total = (resume_score * 0.4) + (aptitude_score * 0.4) + (cert_count * 10)
    feedback = "Excellent readiness!" if total >= 85 else "Keep improving your aptitude and certifications."
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

    # Fetch aptitude and certifications
    c.execute("SELECT score, test_date FROM aptitude WHERE user_id=?", (user_id,))
    aptitude_data = c.fetchall()

    c.execute("SELECT title, date FROM certifications WHERE user_id=?", (user_id,))
    cert_data = c.fetchall()

    conn.close()

    readiness, feedback = calculate_readiness(user_id)

    return render_template('dashboard.html', 
                           user=session['user_name'],
                           aptitude_data=aptitude_data,
                           cert_data=cert_data,
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


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
