from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import hashlib
import os

# Setup paths
base_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__,
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static'))

app.secret_key = 'expense-tracker-secret-2024-xK9mPqL'

# ──────────────────────────────────────────────
# Database setup
# ──────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect('database.db', timeout=20)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS expenses
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  amount REAL,
                  category TEXT,
                  date TEXT,
                  user_id INTEGER)''')

    c.execute("PRAGMA table_info(expenses)")
    columns = [row[1] for row in c.fetchall()]
    if 'user_id' not in columns:
        c.execute("ALTER TABLE expenses ADD COLUMN user_id INTEGER")

    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  password TEXT)''')

    conn.commit()
    conn.close()

init_db()

# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ──────────────────────────────────────────────
# Auth Routes
# ──────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))

    error = None
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = hash_password(request.form['password'])

        conn = sqlite3.connect('database.db', timeout=20)
        c = conn.cursor()
        c.execute("SELECT id, username FROM users WHERE username=? AND password=?",
                  (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('index'))
        else:
            error = 'Invalid username or password.'

    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))

    error = None
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = hash_password(request.form['password'])

        if not username or not request.form['password']:
            error = 'Username and password are required.'
        else:
            try:
                conn = sqlite3.connect('database.db', timeout=20)
                c = conn.cursor()
                c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                          (username, password))
                conn.commit()

                session['user_id'] = c.lastrowid
                session['username'] = username

                return redirect(url_for('index'))

            except sqlite3.IntegrityError:
                error = 'Username already taken.'
            finally:
                conn.close()

    return render_template('register.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ──────────────────────────────────────────────
# HOME ROUTE (FIXED)
# ──────────────────────────────────────────────
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('index'))

# ──────────────────────────────────────────────
# DASHBOARD
# ──────────────────────────────────────────────
@app.route('/dashboard')
@login_required
def index():
    conn = sqlite3.connect('database.db', timeout=20)
    c = conn.cursor()

    c.execute("SELECT * FROM expenses WHERE user_id=? ORDER BY date DESC",
              (session['user_id'],))
    data = c.fetchall()

    total = sum([row[2] for row in data])

    categories = {}
    for row in data:
        cat = row[3]
        categories[cat] = categories.get(cat, 0) + row[2]

    labels = list(categories.keys())
    values = list(categories.values())

    conn.close()

    return render_template('index.html',
                           data=data,
                           total=total,
                           labels=labels,
                           values=values,
                           username=session.get('username'))

# ──────────────────────────────────────────────
# ADD EXPENSE
# ──────────────────────────────────────────────
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name     = request.form['name']
        amount   = request.form['amount']
        category = request.form['category']
        date     = request.form['date']

        conn = sqlite3.connect('database.db', timeout=20)
        c = conn.cursor()

        c.execute("INSERT INTO expenses (name, amount, category, date, user_id) VALUES (?, ?, ?, ?, ?)",
                  (name, amount, category, date, session['user_id']))

        conn.commit()
        conn.close()

        return redirect(url_for('index'))

    return render_template('add.html')

# ──────────────────────────────────────────────
# DELETE
# ──────────────────────────────────────────────
@app.route('/delete/<int:id>')
@login_required
def delete(id):
    conn = sqlite3.connect('database.db', timeout=20)
    c = conn.cursor()

    c.execute("DELETE FROM expenses WHERE id=? AND user_id=?",
              (id, session['user_id']))

    conn.commit()
    conn.close()

    return redirect(url_for('index'))

# ──────────────────────────────────────────────
# RUN
# ──────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True)