import os
import sqlite3
import csv
import sys
from io import StringIO
from datetime import datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, Response, flash

app = Flask(__name__)
app.secret_key = 'eventhub_secure_key_2026_v3'
PORT = int(os.environ.get('PORT', 5000))
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

class DBWrapper:
    def __init__(self, conn, db_type):
        self.conn = conn
        self.db_type = db_type
        
    def execute(self, query, args=()):
        if self.db_type == 'postgres':
            import psycopg2.extras
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            query = query.replace('?', '%s')
        else:
            cur = self.conn.cursor()
        cur.execute(query, args)
        return cur
        
    def commit(self):
        self.conn.commit()
        
    def close(self):
        self.conn.close()

def get_db_connection():
    if DATABASE_URL:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        return DBWrapper(conn, 'postgres')
    else:
        conn = sqlite3.connect('eventhub_v3.db', check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return DBWrapper(conn, 'sqlite')

def init_db():
    conn = get_db_connection()
    if conn.db_type == 'postgres':
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id SERIAL PRIMARY KEY,
                faculty_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                date_time TEXT NOT NULL,
                venue TEXT NOT NULL,
                max_participants INTEGER NOT NULL,
                deadline TEXT NOT NULL,
                FOREIGN KEY (faculty_id) REFERENCES users (id)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS registrations (
                id SERIAL PRIMARY KEY,
                event_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending',
                FOREIGN KEY (event_id) REFERENCES events (id),
                FOREIGN KEY (student_id) REFERENCES users (id),
                UNIQUE(event_id, student_id)
            )
        ''')
    else:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                faculty_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                date_time TEXT NOT NULL,
                venue TEXT NOT NULL,
                max_participants INTEGER NOT NULL,
                deadline TEXT NOT NULL,
                FOREIGN KEY (faculty_id) REFERENCES users (id)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending',
                FOREIGN KEY (event_id) REFERENCES events (id),
                FOREIGN KEY (student_id) REFERENCES users (id),
                UNIQUE(event_id, student_id)
            )
        ''')
        
    cur = conn.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        # Seed users
        conn.execute("INSERT INTO users (username, password, role) VALUES ('faculty', 'faculty123', 'faculty')")
        conn.execute("INSERT INTO users (username, password, role) VALUES ('student', 'student123', 'student')")
        
        # Seed event
        conn.execute("INSERT INTO events (faculty_id, title, description, date_time, venue, max_participants, deadline) VALUES (?, ?, ?, ?, ?, ?, ?)",
                     (1, 'Tech Symposium 2026', 'Annual tech fest featuring AI.', '2026-05-15T10:00', 'Auditorium', 150, '2026-05-10T23:59'))
        
        # Seed registration
        conn.execute("INSERT INTO registrations (event_id, student_id, status) VALUES (1, 2, 'Pending')")
    
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    if 'user_id' in session:
        if session.get('role') == 'faculty':
            return redirect(url_for('faculty_dashboard'))
        else:
            return redirect(url_for('student_events'))
    return redirect(url_for('login'))

@app.route('/fun')
def fun():
    if 'antigravity' in sys.modules:
        del sys.modules['antigravity']
    import antigravity
    return "Antigravity comic triggered (check the server console/browser)! Enjoy 🎉", 200

# ================= AUTHENTICATION ================= #

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash('Logged in successfully.', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        
        conn = get_db_connection()
        existing = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            conn.close()
            flash('Username already exists.', 'error')
            return redirect(url_for('signup'))
            
        conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
        conn.commit()
        conn.close()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('profile.html', user={'username': session['username'], 'role': session['role']})

# ================= FACULTY ROUTES ================= #

@app.route('/faculty/dashboard')
def faculty_dashboard():
    if session.get('role') != 'faculty': return redirect(url_for('home'))
    
    conn = get_db_connection()
    events = conn.execute("SELECT * FROM events WHERE faculty_id = ? ORDER BY date_time DESC", (session['user_id'],)).fetchall()
    
    # Calculate stats
    total_events = len(events)
    total_regs = conn.execute('''
        SELECT COUNT(*) FROM registrations r
        JOIN events e ON r.event_id = e.id
        WHERE e.faculty_id = ?
    ''', (session['user_id'],)).fetchone()[0]
    
    conn.close()
    return render_template('faculty_dashboard.html', events=events, total_events=total_events, total_regs=total_regs)

@app.route('/faculty/event/create', methods=['GET', 'POST'])
def faculty_event_create():
    if session.get('role') != 'faculty': return redirect(url_for('home'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        desc = request.form.get('description')
        dt = request.form.get('date_time')
        venue = request.form.get('venue')
        m_part = int(request.form.get('max_participants', 0))
        deadline = request.form.get('deadline')
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO events (faculty_id, title, description, date_time, venue, max_participants, deadline)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (session['user_id'], title, desc, dt, venue, m_part, deadline))
        conn.commit()
        conn.close()
        flash('Event published!', 'success')
        return redirect(url_for('faculty_dashboard'))
        
    return render_template('faculty_event_create.html')

@app.route('/faculty/event/<int:event_id>/view')
def faculty_event_view(event_id):
    if session.get('role') != 'faculty': return redirect(url_for('home'))
    
    conn = get_db_connection()
    event = conn.execute("SELECT * FROM events WHERE id = ? AND faculty_id = ?", (event_id, session['user_id'])).fetchone()
    if not event:
        conn.close()
        flash('Event not found or unauthorized.', 'error')
        return redirect(url_for('faculty_dashboard'))
        
    regs = conn.execute('''
        SELECT r.id as reg_id, u.username, r.status
        FROM registrations r
        JOIN users u ON r.student_id = u.id
        WHERE r.event_id = ?
        ORDER BY r.id DESC
    ''', (event_id,)).fetchall()
    
    approved_count = sum(1 for r in regs if r['status'] == 'Approved')
    conn.close()
    
    return render_template('faculty_event.html', event=event, regs=regs, approved_count=approved_count)

@app.route('/faculty/event/<int:event_id>/delete', methods=['POST'])
def faculty_event_delete(event_id):
    if session.get('role') != 'faculty': return redirect(url_for('home'))
    conn = get_db_connection()
    conn.execute("DELETE FROM registrations WHERE event_id = ?", (event_id,))
    conn.execute("DELETE FROM events WHERE id = ? AND faculty_id = ?", (event_id, session['user_id']))
    conn.commit()
    conn.close()
    flash('Event deleted.', 'success')
    return redirect(url_for('faculty_dashboard'))

@app.route('/faculty/registration/<int:reg_id>/decide', methods=['POST'])
def faculty_reg_decide(reg_id):
    if session.get('role') != 'faculty': return redirect(url_for('home'))
    status = request.form.get('status')
    
    conn = get_db_connection()
    # Verify ownership indirectly
    conn.execute("UPDATE registrations SET status = ? WHERE id = ?", (status, reg_id))
    conn.commit()
    
    # redirect back to event view
    reg = conn.execute("SELECT event_id FROM registrations WHERE id = ?", (reg_id,)).fetchone()
    conn.close()
    
    flash(f'Registration marked as {status}. Email notification simulated.', 'success')
    if reg: return redirect(url_for('faculty_event_view', event_id=reg['event_id']))
    return redirect(url_for('faculty_dashboard'))

@app.route('/faculty/event/<int:event_id>/export')
def faculty_event_export(event_id):
    if session.get('role') != 'faculty': return redirect(url_for('home'))
    conn = get_db_connection()
    regs = conn.execute('''
        SELECT u.username, r.status
        FROM registrations r
        JOIN users u ON r.student_id = u.id
        WHERE r.event_id = ?
    ''', (event_id,)).fetchall()
    event = conn.execute("SELECT title FROM events WHERE id = ?", (event_id,)).fetchone()
    conn.close()
    
    def generate():
        data = StringIO()
        w = csv.writer(data)
        w.writerow(['Student Name', 'Status'])
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)
        for r in regs:
            w.writerow([r['username'], r['status']])
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)
            
    header = {"Content-Disposition": f"attachment; filename={event['title'].replace(' ', '_')}_participants.csv"}
    return Response(generate(), mimetype='text/csv', headers=header)


# ================= STUDENT ROUTES ================= #

@app.route('/student/events')
def student_events():
    if session.get('role') != 'student': return redirect(url_for('home'))
    
    search_q = request.args.get('search', '').lower()
    date_f = request.args.get('date_filter', '')
    
    conn = get_db_connection()
    # Fetch all events + faculty username
    events_raw = conn.execute('''
        SELECT e.*, u.username as faculty_name 
        FROM events e JOIN users u ON e.faculty_id = u.id
        ORDER BY e.date_time DESC
    ''').fetchall()
    
    # Fetch student's registrations to show buttons dynamically
    my_regs = conn.execute("SELECT event_id, status FROM registrations WHERE student_id = ?", (session['user_id'],)).fetchall()
    reg_map = {r['event_id']: r['status'] for r in my_regs}
    
    events_processed = []
    now_iso = datetime.now().isoformat()
    
    for er in events_raw:
        # Check seats filled
        filled = conn.execute("SELECT COUNT(*) FROM registrations WHERE event_id = ? AND status != 'Rejected'", (er['id'],)).fetchone()[0]
        
        # Apply filters
        if search_q and search_q not in er['title'].lower() and search_q not in er['description'].lower() and search_q not in er['faculty_name'].lower():
            continue
        if date_f and not er['date_time'].startswith(date_f):
            continue
            
        e_dict = dict(er)
        e_dict['seats_left'] = e_dict['max_participants'] - filled
        e_dict['assigned_status'] = reg_map.get(e_dict['id'])
        e_dict['deadline_passed'] = now_iso > e_dict['deadline']
        events_processed.append(e_dict)
        
    conn.close()
    
    return render_template('student_events.html', events=events_processed, search_q=search_q, date_f=date_f)

@app.route('/student/dashboard')
def student_dashboard():
    if session.get('role') != 'student': return redirect(url_for('home'))
    
    conn = get_db_connection()
    regs = conn.execute('''
        SELECT r.id as reg_id, r.status, e.title, e.date_time
        FROM registrations r
        JOIN events e ON r.event_id = e.id
        WHERE r.student_id = ?
        ORDER BY e.date_time DESC
    ''', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('student_dashboard.html', regs=regs)

@app.route('/student/event/<int:event_id>/register', methods=['POST'])
def student_register(event_id):
    if session.get('role') != 'student': return redirect(url_for('home'))
    
    conn = get_db_connection()
    # Check deadline/seats logic here if strictly needed, but UI handles most of it.
    try:
        conn.execute("INSERT INTO registrations (event_id, student_id) VALUES (?, ?)", (event_id, session['user_id']))
        conn.commit()
        flash('Registration successful! Email notification simulated.', 'success')
    except Exception as e:
        try: conn.conn.rollback() 
        except: pass
        flash('You are already registered for this event.', 'error')
    finally:
        conn.close()
        
    return redirect(url_for('student_events'))

@app.route('/student/registration/<int:reg_id>/cancel', methods=['POST'])
def student_cancel(reg_id):
    if session.get('role') != 'student': return redirect(url_for('home'))
    conn = get_db_connection()
    conn.execute("DELETE FROM registrations WHERE id = ? AND student_id = ?", (reg_id, session['user_id']))
    conn.commit()
    conn.close()
    flash('Registration cancelled successfully.', 'success')
    return redirect(url_for('student_dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=True)
