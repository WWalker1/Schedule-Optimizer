from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
from flask import jsonify
from flask_cors import CORS
import ml_utils  # Import our ML utilities

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
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
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('register'))
        
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
        board_type = request.form['board_type']
        conn = get_db_connection()
        conn.execute('INSERT INTO habit_boards (user_id, name, description, board_type) VALUES (?, ?, ?, ?)',
                     (session['user_id'], name, description, board_type))
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
    conn = get_db_connection()
    board = conn.execute('SELECT * FROM habit_boards WHERE id = ? AND user_id = ?', 
                         (board_id, session['user_id'])).fetchone()
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        variable_type = request.form['variable_type']
        
        # Only set frequency for time-series boards
        frequency = request.form.get('frequency') if board['board_type'] == 'time-series' else None
        
        cursor = conn.cursor()
        cursor.execute('INSERT INTO habits (user_id, board_id, name, description, frequency, variable_type) VALUES (?, ?, ?, ?, ?, ?)',
                     (session['user_id'], board_id, name, description, frequency, variable_type))
        habit_id = cursor.lastrowid
        
        if variable_type == 'categorical':
            options = request.form.getlist('options[]')
            for option in options:
                if option.strip():  # Only add non-empty options
                    cursor.execute('INSERT INTO habit_options (habit_id, option_value) VALUES (?, ?)',
                                   (habit_id, option.strip()))
        
        conn.commit()
        conn.close()
        flash('New habit added successfully')
        return redirect(url_for('view_board', board_id=board_id))
    
    conn.close()
    return render_template('add_habit.html', board_id=board_id, board=board)

@app.route('/board/<int:board_id>/log_all', methods=['GET', 'POST'])
@login_required
def log_all_habits(board_id):
    conn = get_db_connection()
    board = conn.execute('SELECT * FROM habit_boards WHERE id = ? AND user_id = ?', 
                         (board_id, session['user_id'])).fetchone()
    
    # Get today's date
    today = datetime.now().date()

    if request.method == 'POST':
        log_date = request.form['log_date']
        for key, value in request.form.items():
            if key.startswith('habit_'):
                habit_id = int(key.split('_')[1])
                if value:  # Only log if a value is provided (not blank)
                    # Check if an entry already exists for this date and habit
                    existing = conn.execute('SELECT id FROM entries WHERE habit_id = ? AND date = ?', 
                                           (habit_id, log_date)).fetchone()
                    if existing:
                        # Update existing entry
                        conn.execute('UPDATE entries SET value = ? WHERE id = ?', 
                                     (value, existing['id']))
                    else:
                        # Create new entry
                        conn.execute('INSERT INTO entries (habit_id, date, value) VALUES (?, ?, ?)',
                                     (habit_id, log_date, value))
        conn.commit()
        flash('Habits logged successfully')
        return redirect(url_for('view_board', board_id=board_id))

    # Fetch habits and their recent entries
    habits_to_log = []
    habits = conn.execute('SELECT * FROM habits WHERE board_id = ?', (board_id,)).fetchall()
    for habit in habits:
        # Get the most recent entry for this habit
        last_entry = conn.execute('''
            SELECT date FROM entries 
            WHERE habit_id = ? 
            ORDER BY date DESC LIMIT 1
        ''', (habit['id'],)).fetchone()

        # Get options for categorical habits
        if habit['variable_type'] == 'categorical':
            options = conn.execute('SELECT option_value FROM habit_options WHERE habit_id = ?', (habit['id'],)).fetchall()
            habit = dict(habit)
            habit['options'] = [option['option_value'] for option in options]

        # Determine if the habit should be logged today
        should_log = True
        if last_entry:
            last_date = datetime.strptime(last_entry['date'], '%Y-%m-%d').date()
            days_since_last = (today - last_date).days
            if habit['frequency'] == 'daily' and days_since_last < 1:
                should_log = False
            elif habit['frequency'] == 'weekly' and days_since_last < 7:
                should_log = False
            elif habit['frequency'] == 'monthly' and days_since_last < 30:
                should_log = False

        if should_log:
            habits_to_log.append(habit)

    conn.close()
    return render_template('log_all_habits.html', board=board, habits=habits_to_log, today=today.isoformat())

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

@app.route('/board/<int:board_id>/delete', methods=['POST'])
@login_required
def delete_board(board_id):
    conn = get_db_connection()
    
    # First, delete all entries associated with habits in this board
    conn.execute('''
        DELETE FROM entries 
        WHERE habit_id IN (SELECT id FROM habits WHERE board_id = ?)
    ''', (board_id,))
    
    # Delete all habit options associated with habits in this board
    conn.execute('''
        DELETE FROM habit_options 
        WHERE habit_id IN (SELECT id FROM habits WHERE board_id = ?)
    ''', (board_id,))
    
    # Delete all habits associated with this board
    conn.execute('DELETE FROM habits WHERE board_id = ?', (board_id,))
    
    # Finally, delete the board itself
    conn.execute('DELETE FROM habit_boards WHERE id = ? AND user_id = ?', (board_id, session['user_id']))
    
    conn.commit()
    conn.close()
    
    flash('Habit board deleted successfully')
    return redirect(url_for('boards'))

@app.route('/stats')
@login_required
def stats():
    conn = get_db_connection()
    habits = conn.execute('SELECT id, name, variable_type FROM habits WHERE user_id = ?', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('stats.html', habits=habits)

@app.route('/models', methods=['GET', 'POST'])
@login_required
def models():
    conn = get_db_connection()
    # Get all user's habits that have sufficient data for modeling
    habits = conn.execute('''
        SELECT h.id, h.name, h.variable_type, COUNT(e.id) as entry_count 
        FROM habits h
        LEFT JOIN entries e ON h.id = e.habit_id
        WHERE h.user_id = ?
        GROUP BY h.id
        HAVING entry_count >= 10
    ''', (session['user_id'],)).fetchall()
    
    # Get all numeric/boolean habits that could be target variables
    target_habits = [h for h in habits if h['variable_type'] in ('numeric', 'boolean')]
    
    # Get all habits that could be features
    feature_habits = [h for h in habits if h['entry_count'] >= 10]
    
    if request.method == 'POST':
        target_habit_id = request.form['target_habit']
        feature_habit_ids = request.form.getlist('feature_habits')
        optimization_goal = request.form['optimization_goal']  # 'maximize' or 'minimize'
        model_type = request.form['model_type']  # 'random_forest', 'svm', etc.
        
        # Fetch the target habit details
        target_habit = conn.execute('SELECT * FROM habits WHERE id = ?', (target_habit_id,)).fetchone()
        
        # Fetch data for the target and feature habits
        data = {}
        
        # Get target data
        target_data = conn.execute('''
            SELECT date, value FROM entries 
            WHERE habit_id = ? 
            ORDER BY date
        ''', (target_habit_id,)).fetchall()
        
        data['target'] = {
            'name': target_habit['name'],
            'dates': [entry['date'] for entry in target_data],
            'values': [float(entry['value']) if target_habit['variable_type'] == 'numeric' 
                      else 1 if entry['value'].lower() in ('true', '1', 'yes') else 0 
                      for entry in target_data]
        }
        
        # Get feature data
        data['features'] = []
        for feature_id in feature_habit_ids:
            feature = conn.execute('SELECT * FROM habits WHERE id = ?', (feature_id,)).fetchone()
            feature_data = conn.execute('''
                SELECT date, value FROM entries 
                WHERE habit_id = ? 
                ORDER BY date
            ''', (feature_id,)).fetchall()
            
            feature_values = []
            if feature['variable_type'] == 'numeric':
                feature_values = [float(entry['value']) for entry in feature_data]
            elif feature['variable_type'] == 'boolean':
                feature_values = [1 if entry['value'].lower() in ('true', '1', 'yes') else 0 for entry in feature_data]
            elif feature['variable_type'] == 'categorical':
                # Get unique categories
                categories = conn.execute('''
                    SELECT DISTINCT value FROM entries WHERE habit_id = ?
                ''', (feature_id,)).fetchall()
                categories = [c['value'] for c in categories]
                
                # One-hot encode categorical values
                for entry in feature_data:
                    encoded = [1 if entry['value'] == cat else 0 for cat in categories]
                    feature_values.append(encoded)
            
            data['features'].append({
                'id': feature['id'],
                'name': feature['name'],
                'type': feature['variable_type'],
                'dates': [entry['date'] for entry in feature_data],
                'values': feature_values
            })
        
        # Process data and train model
        try:
            # Preprocess data
            X, y, feature_names = ml_utils.preprocess_data(data)
            
            # Train model
            is_classification = target_habit['variable_type'] == 'boolean'
            model, scaler, X_test, y_test, accuracy = ml_utils.train_model(X, y, model_type, is_classification)
            
            # Generate recommendations
            recommendations = ml_utils.generate_recommendations(data, model, scaler, feature_names, optimization_goal)
            
            conn.close()
            return render_template('model_results.html', 
                                  target_habit=target_habit,
                                  recommendations=recommendations,
                                  optimization_goal=optimization_goal)
        except Exception as e:
            flash(f"Error training model: {str(e)}")
            conn.close()
            return redirect(url_for('models'))
    
    conn.close()
    return render_template('models.html', target_habits=target_habits, feature_habits=feature_habits)

@app.route('/optimize_schedule', methods=['GET', 'POST'])
@login_required
def optimize_schedule():
    conn = get_db_connection()
    habits = conn.execute('SELECT * FROM habits WHERE user_id = ?', (session['user_id'],)).fetchall()
    
    if request.method == 'POST':
        target_habit_id = request.form['target_habit']
        constraints = {}
        
        # Collect constraints for each habit
        for habit in habits:
            habit_id = habit['id']
            min_key = f'min_{habit_id}'
            max_key = f'max_{habit_id}'
            
            if min_key in request.form and request.form[min_key]:
                if habit_id not in constraints:
                    constraints[habit_id] = {}
                constraints[habit_id]['min'] = float(request.form[min_key])
            
            if max_key in request.form and request.form[max_key]:
                if habit_id not in constraints:
                    constraints[habit_id] = {}
                constraints[habit_id]['max'] = float(request.form[max_key])
        
        # Generate optimized schedule
        schedule = ml_utils.generate_optimized_schedule(target_habit_id, constraints, habits)
        
        conn.close()
        return render_template('optimized_schedule.html', schedule=schedule)
    
    conn.close()
    return render_template('optimize_schedule.html', habits=habits)

@app.route('/generate_plot', methods=['POST'])
@login_required
def generate_plot():
    habit_id = request.form['habit_id']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    
    conn = get_db_connection()
    habit = conn.execute('SELECT variable_type FROM habits WHERE id = ?', (habit_id,)).fetchone()
    if habit['variable_type'] == 'numeric':
        entries = conn.execute('''
            SELECT date, value FROM entries 
            WHERE habit_id = ? AND date BETWEEN ? AND ?
            ORDER BY date
        ''', (habit_id, start_date, end_date)).fetchall()
        dates = [entry['date'] for entry in entries]
        values = [float(entry['value']) for entry in entries]
        
        data = [{
            'x': dates,
            'y': values,
            'type': 'scatter'
        }]
        
        layout = {
            'title': 'Habit Progress',
            'xaxis': {'title': 'Date'},
            'yaxis': {'title': 'Value'}
        }
    elif habit['variable_type'] == 'boolean':
        entries = conn.execute('''
            SELECT date, value FROM entries 
            WHERE habit_id = ? AND date BETWEEN ? AND ?
            ORDER BY date
        ''', (habit_id, start_date, end_date)).fetchall()
        dates = [entry['date'] for entry in entries]
        values = [int(entry['value']) for entry in entries]
        
        data = [{
            'x': dates,
            'y': values,
            'type': 'bar'
        }]
        
        layout = {
            'title': 'Habit Progress',
            'xaxis': {'title': 'Date'},
            'yaxis': {'title': 'Yes/No'}
        }
    elif habit['variable_type'] == 'categorical':
        entries = conn.execute('''
            SELECT date, value FROM entries 
            WHERE habit_id = ? AND date BETWEEN ? AND ?
            ORDER BY date
        ''', (habit_id, start_date, end_date)).fetchall()
        dates = [entry['date'] for entry in entries]
        values = [entry['value'] for entry in entries]
        
        data = [{
            'x': dates,
            'y': values,
            'type': 'bar'
        }]
        
        layout = {
            'title': 'Habit Progress',
            'xaxis': {'title': 'Date'},
            'yaxis': {'title': 'Category'}
        }
    
    conn.close()
    
    return jsonify({'data': data, 'layout': layout})

@app.route('/habit/<int:habit_id>')
@login_required
def view_habit(habit_id):
    conn = get_db_connection()
    habit = conn.execute('SELECT * FROM habits WHERE id = ? AND user_id = ?', 
                         (habit_id, session['user_id'])).fetchone()
    entries = conn.execute('SELECT * FROM entries WHERE habit_id = ? ORDER BY date DESC', (habit_id,)).fetchall()
    
    habit_options = []
    if habit['variable_type'] == 'categorical':
        options = conn.execute('SELECT option_value FROM habit_options WHERE habit_id = ?', (habit_id,)).fetchall()
        habit_options = [option['option_value'] for option in options]
    
    conn.close()
    return render_template('view_habit.html', habit=habit, entries=entries, habit_options=habit_options)

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

@app.route('/habit/<int:habit_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_habit(habit_id):
    conn = get_db_connection()
    habit = conn.execute('SELECT * FROM habits WHERE id = ? AND user_id = ?', 
                         (habit_id, session['user_id'])).fetchone()
    board = conn.execute('SELECT * FROM habit_boards WHERE id = ?', (habit['board_id'],)).fetchone()
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        frequency = request.form.get('frequency') if board['board_type'] == 'time-series' else None

        conn.execute('''UPDATE habits 
                        SET name = ?, description = ?, frequency = ?
                        WHERE id = ?''', 
                     (name, description, frequency, habit_id))

        # Handle categorical options
        if habit['variable_type'] == 'categorical':
            # Delete existing options
            conn.execute('DELETE FROM habit_options WHERE habit_id = ?', (habit_id,))
            # Add new options
            options = request.form.getlist('options[]')
            for option in options:
                if option.strip():
                    conn.execute('INSERT INTO habit_options (habit_id, option_value) VALUES (?, ?)',
                                 (habit_id, option.strip()))

        conn.commit()
        flash('Habit updated successfully')
        return redirect(url_for('view_board', board_id=habit['board_id']))

    # Fetch categorical options if applicable
    options = []
    if habit['variable_type'] == 'categorical':
        options = conn.execute('SELECT option_value FROM habit_options WHERE habit_id = ?', 
                              (habit_id,)).fetchall()
        options = [option['option_value'] for option in options]

    conn.close()
    return render_template('edit_habit.html', habit=habit, board=board, options=options)

@app.route('/habit/<int:habit_id>/delete', methods=['POST'])
@login_required
def delete_habit(habit_id):
    conn = get_db_connection()
    habit = conn.execute('SELECT board_id FROM habits WHERE id = ? AND user_id = ?', 
                         (habit_id, session['user_id'])).fetchone()
    
    if habit:
        # Delete related entries and options first
        conn.execute('DELETE FROM entries WHERE habit_id = ?', (habit_id,))
        conn.execute('DELETE FROM habit_options WHERE habit_id = ?', (habit_id,))
        # Then delete the habit
        conn.execute('DELETE FROM habits WHERE id = ?', (habit_id,))
        conn.commit()
        flash('Habit deleted successfully')
    else:
        flash('Habit not found or unauthorized')
    
    conn.close()
    return redirect(url_for('view_board', board_id=habit['board_id']))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
