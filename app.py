from functools import wraps
from flask import Flask, abort, flash, make_response, render_template, request, redirect, session, url_for, send_from_directory
import os
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('STUDYNOVA_SECRET_KEY', 'studynova-dev-secret-key')
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
DATABASE = os.path.join(os.path.dirname(__file__), 'studynova.db')

MYSQL_CONFIG = {
    'host': os.environ.get('MYSQL_HOST', 'localhost'),
    'port': int(os.environ.get('MYSQL_PORT', 3306)),
    'user': os.environ.get('MYSQL_USER', 'studynova'),
    'password': os.environ.get('MYSQL_PASSWORD', 'studynova'),
    'database': os.environ.get('MYSQL_DATABASE', 'studynova'),
}

USE_MYSQL = all([
    os.environ.get('MYSQL_HOST'),
    os.environ.get('MYSQL_USER'),
    os.environ.get('MYSQL_PASSWORD'),
    os.environ.get('MYSQL_DATABASE'),
])

try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    mysql = None
    MYSQL_AVAILABLE = False


def mysql_enabled():
    return USE_MYSQL and MYSQL_AVAILABLE


def get_db_connection():
    if mysql_enabled():
        return mysql.connector.connect(
            host=MYSQL_CONFIG['host'],
            port=MYSQL_CONFIG['port'],
            user=MYSQL_CONFIG['user'],
            password=MYSQL_CONFIG['password'],
            database=MYSQL_CONFIG['database'],
        )

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def get_placeholder():
    return '%s' if mysql_enabled() else '?'


def execute_query(sql, params=None, fetchone=False, fetchall=False, commit=False):
    params = params or ()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) if mysql_enabled() else conn.cursor()
    try:
        cursor.execute(sql, params)
        if commit:
            conn.commit()
        if fetchone:
            return cursor.fetchone()
        if fetchall:
            return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


# Read a user record by email address.
def get_user_by_email(email):
    placeholder = get_placeholder()
    query = f'SELECT * FROM users WHERE email = {placeholder}'
    return execute_query(query, (email,), fetchone=True)

# Create a new user account and store a hashed password.
def create_user(username, email, password):
    placeholder = get_placeholder()
    hashed_password = generate_password_hash(password)
    query = f'INSERT INTO users (username, email, password) VALUES ({placeholder}, {placeholder}, {placeholder})'
    execute_query(query, (username, email, hashed_password), commit=True)


def init_db():
    return

notes = [
    {
        'id': 1,
        'title': 'Introduction to Python',
        'subject': 'Python',
        'category': 'Python',
        'filename': 'python_intro.pdf',
        'date': '2026-05-20',
        'extension': 'pdf'
    },
    {
        'id': 2,
        'title': 'Database Management Systems',
        'subject': 'DBMS',
        'category': 'DBMS',
        'filename': 'dbms_notes.docx',
        'date': '2026-05-22',
        'extension': 'docx'
    }
]

def get_file_icon(extension):
    icons = {
        'pdf': 'fas fa-file-pdf text-danger',
        'ppt': 'fas fa-file-powerpoint text-warning',
        'pptx': 'fas fa-file-powerpoint text-warning',
        'doc': 'fas fa-file-word text-primary',
        'docx': 'fas fa-file-word text-primary',
        'zip': 'fas fa-file-archive text-secondary',
        'jpg': 'fas fa-file-image text-success',
        'jpeg': 'fas fa-file-image text-success',
        'png': 'fas fa-file-image text-success'
    }
    return icons.get(extension.lower(), 'fas fa-file text-muted')

for note in notes:
    note['icon'] = get_file_icon(note['extension'])

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get('user_email'):
            flash('Please login to continue.', 'warning')
            return redirect(url_for('login', next=request.path))
        return view(*args, **kwargs)
    return wrapped_view

def find_note_by_filename(filename):
    return next((note for note in notes if note['filename'] == filename), None)

def demo_note_content(note):
    return (
        f"{note['title']}\n"
        f"Subject: {note['subject']}\n"
        f"Category: {note['category']}\n"
        f"Uploaded: {note['date']}\n\n"
        "This is a demo StudyNova note preview. Upload your own files to replace "
        "these sample materials with real PDFs, PPTs, documents, code resources, "
        "and study notes."
    )

@app.route('/')
@login_required
def home():
    # Show only latest 3 notes on home page
    latest_notes = notes[-3:][::-1]
    stats = {
        'total_notes': len(notes),
        'total_users': 150,  # Dummy data
        'downloads': 1200    # Dummy data
    }
    return render_template('index.html', notes=latest_notes, stats=stats)

@app.route('/dashboard')
@login_required
def dashboard():
    return redirect(url_for('home'))

@app.route('/notes')
@login_required
def notes_library():
    category = request.args.get('category')
    search = request.args.get('search')
    
    filtered_notes = notes
    if category and category != 'All':
        filtered_notes = [n for n in filtered_notes if n['category'] == category]
    if search:
        filtered_notes = [n for n in filtered_notes if search.lower() in n['title'].lower() or search.lower() in n['subject'].lower()]
        
    categories = ['All', 'CSE', 'AI', 'Python', 'DBMS', 'Web Development', 'Data Science', 'Java']
    return render_template('notes.html', notes=filtered_notes[::-1], categories=categories, current_category=category or 'All')

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        title = request.form['title']
        subject = request.form['subject']
        category = request.form['category']
        file = request.files['file']

        if file:
            filename = secure_filename(file.filename)
            extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            new_note = {
                'id': len(notes) + 1,
                'title': title,
                'subject': subject,
                'category': category,
                'filename': filename,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'extension': extension,
                'icon': get_file_icon(extension)
            }
            notes.append(new_note)

            return redirect(url_for('notes_library'))

    categories = ['CSE', 'AI', 'Python', 'DBMS', 'Web Development', 'Data Science', 'Java']
    return render_template('upload.html', categories=categories)

@app.route('/about')
@login_required
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
@login_required
def contact():
    if request.method == 'POST':
        # Handle contact form submission
        return redirect(url_for('home'))
    return render_template('contact.html')

@app.route('/download/<filename>')
@login_required
def download(filename):
    safe_filename = secure_filename(filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
    if not os.path.exists(filepath):
        note = find_note_by_filename(safe_filename)
        if not note:
            abort(404)
        response = make_response(demo_note_content(note))
        response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename="{os.path.splitext(safe_filename)[0]}-demo.txt"'
        return response
    return send_from_directory(app.config['UPLOAD_FOLDER'], safe_filename, as_attachment=True)

@app.route('/preview/<filename>')
@login_required
def preview(filename):
    safe_filename = secure_filename(filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
    if not os.path.exists(filepath):
        note = find_note_by_filename(safe_filename)
        if not note:
            abort(404)
        return render_template('preview.html', note=note, content=demo_note_content(note))
    return send_from_directory(app.config['UPLOAD_FOLDER'], safe_filename, as_attachment=False)

@app.route('/login', methods=['GET', 'POST'])
def login():
    email = ''
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return render_template('login.html', email=email)

        user = get_user_by_email(email)
        if user and check_password_hash(user['password'], password):
            session.clear()
            session.permanent = True
            session['user_email'] = email
            session['user_name'] = user['username']
            flash('Login successful. Welcome back!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page if next_page and next_page.startswith('/') else url_for('dashboard'))

        flash('Invalid email or password.', 'danger')
        return render_template('login.html', email=email)

    return render_template('login.html', email=email)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        accepted_terms = request.form.get('terms') == 'on'

        if not all([username, email, password, confirm_password]):
            flash('Please fill all registration fields.', 'danger')
            return render_template('register.html', username=username, email=email)
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html', username=username, email=email)
        if not accepted_terms:
            flash('Please accept the Terms & Conditions.', 'danger')
            return render_template('register.html', username=username, email=email)
        if get_user_by_email(email):
            flash('This email is already registered. Please login.', 'warning')
            return redirect(url_for('login'))

        create_user(username, email, password)
        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', username='', email='')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        user = get_user_by_email(email)
        if not user:
            flash('No account found with that email. Please register first.', 'danger')
            return render_template('forgot_password.html')
        if not password or password != confirm_password:
            flash('Please enter matching new passwords.', 'danger')
            return render_template('forgot_password.html')

        update_placeholder = get_placeholder()
        update_query = f'UPDATE users SET password = {update_placeholder} WHERE email = {update_placeholder}'
        execute_query(update_query, (generate_password_hash(password), email), commit=True)

        flash('Password updated. Please login with your new password.', 'success')
        return redirect(url_for('login'))

    return render_template('forgot_password.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)