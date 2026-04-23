from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# Create database
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS expenses
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  amount REAL,
                  category TEXT,
                  date TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM expenses")
    data = c.fetchall()

    total = sum([row[2] for row in data])

    # Chart data
    categories = {}
    for row in data:
        cat = row[3]
        categories[cat] = categories.get(cat, 0) + row[2]

    labels = list(categories.keys())
    values = list(categories.values())

    conn.close()
    return render_template('index.html', data=data, total=total, labels=labels, values=values)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        name = request.form['name']
        amount = request.form['amount']
        category = request.form['category']
        date = request.form['date']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO expenses (name, amount, category, date) VALUES (?, ?, ?, ?)", 
                  (name, amount, category, date))
        conn.commit()
        conn.close()

        return redirect('/')
    
    return render_template('add.html')

@app.route('/delete/<int:id>')
def delete(id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM expenses WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)