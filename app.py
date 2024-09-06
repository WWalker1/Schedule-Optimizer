from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key

def get_db_connection():
    conn = sqlite3.connect('habits.db')
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    habits = conn.execute('SELECT * FROM habits WHERE user_id = ?', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('index.html', habits=habits)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        
        if conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone() is not None:
            flash('Username already exists')
        else:
            conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                         (username, generate_password_hash(password)))
            conn.commit()
            flash('Registration successful')
            return redirect(url_for('login'))
        
        conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            flash('Logged in successfully')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully')
    return redirect(url_for('login'))

@app.route('/boards', methods=['GET', 'POST'])
@login_required
def boards():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        conn = get_db_connection()
        conn.execute('INSERT INTO habit_boards (user_id, name, description) VALUES (?, ?, ?)',
                     (session['user_id'], name, description))
        conn.commit()
        conn.close()
        flash('New board created successfully')
        return redirect(url_for('boards'))
    
    conn = get_db_connection()
    boards = conn.execute('SELECT * FROM habit_boards WHERE user_id = ?', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('boards.html', boards=boards)

@app.route('/board/<int:board_id>')
@login_required
def view_board(board_id):
    conn = get_db_connection()
    board = conn.execute('SELECT * FROM habit_boards WHERE id = ? AND user_id = ?', 
                         (board_id, session['user_id'])).fetchone()
    habits = conn.execute('SELECT * FROM habits WHERE board_id = ?', (board_id,)).fetchall()
    conn.close()
    return render_template('view_board.html', board=board, habits=habits)

@app.route('/board/<int:board_id>/add_habit', methods=['GET', 'POST'])
@login_required
def add_habit(board_id):
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        frequency = request.form['frequency']
        variable_type = request.form['variable_type']
        conn = get_db_connection()
        conn.execute('INSERT INTO habits (user_id, board_id, name, description, frequency, variable_type) VALUES (?, ?, ?, ?, ?, ?)',
                     (session['user_id'], board_id, name, description, frequency, variable_type))
        conn.commit()
        conn.close()
        flash('New habit added successfully')
        return redirect(url_for('view_board', board_id=board_id))
    
    return render_template('add_habit.html', board_id=board_id)

@app.route('/habit/<int:habit_id>/log', methods=['GET', 'POST'])
@login_required
def log_habit(habit_id):
    conn = get_db_connection()
    habit = conn.execute('SELECT * FROM habits WHERE id = ? AND user_id = ?', 
                         (habit_id, session['user_id'])).fetchone()
    
    if request.method == 'POST':
        date = request.form['date']
        value = request.form['value']
        conn.execute('INSERT INTO entries (habit_id, date, value) VALUES (?, ?, ?)',
                     (habit_id, date, value))
        conn.commit()
        flash('Habit logged successfully')
        return redirect(url_for('view_habit', habit_id=habit_id))
    
    entries = conn.execute('SELECT * FROM entries WHERE habit_id = ? ORDER BY date DESC', (habit_id,)).fetchall()
    conn.close()
    return render_template('log_habit.html', habit=habit, entries=entries)

@app.route('/habit/<int:habit_id>')
@login_required
def view_habit(habit_id):
    conn = get_db_connection()
    habit = conn.execute('SELECT * FROM habits WHERE id = ? AND user_id = ?', 
                         (habit_id, session['user_id'])).fetchone()
    entries = conn.execute('SELECT * FROM entries WHERE habit_id = ? ORDER BY date DESC', (habit_id,)).fetchall()
    conn.close()
    return render_template('view_habit.html', habit=habit, entries=entries)

@app.route('/entry/<int:entry_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_entry(entry_id):
    conn = get_db_connection()
    entry = conn.execute('SELECT * FROM entries WHERE id = ?', (entry_id,)).fetchone()
    habit = conn.execute('SELECT * FROM habits WHERE id = ? AND user_id = ?', 
                         (entry['habit_id'], session['user_id'])).fetchone()
    
    if request.method == 'POST':
        value = request.form['value']
        conn.execute('UPDATE entries SET value = ? WHERE id = ?', (value, entry_id))
        conn.commit()
        flash('Entry updated successfully')
        return redirect(url_for('view_habit', habit_id=habit['id']))
    
    conn.close()
    return render_template('edit_entry.html', entry=entry, habit=habit)

@app.route('/entry/<int:entry_id>/delete', methods=['POST'])
@login_required
def delete_entry(entry_id):
    conn = get_db_connection()
    entry = conn.execute('SELECT * FROM entries WHERE id = ?', (entry_id,)).fetchone()
    habit = conn.execute('SELECT * FROM habits WHERE id = ? AND user_id = ?', 
                         (entry['habit_id'], session['user_id'])).fetchone()
    
    conn.execute('DELETE FROM entries WHERE id = ?', (entry_id,))
    conn.commit()
    conn.close()
    flash('Entry deleted successfully')
    return redirect(url_for('view_habit', habit_id=habit['id']))



if __name__ == '__main__':
    app.run(debug=True)
