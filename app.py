import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash
import database
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev_secret_key'

# Initialize DB on startup
os.makedirs('instance', exist_ok=True)
with app.app_context():
    database.init_db(app)

@app.teardown_appcontext
def close_connection(exception):
    database.close_connection(exception)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_user():
    user = None
    if 'user_id' in session:
        db = database.get_db()
        user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    return dict(current_user=user)

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = database.get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            try:
                db.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                db.commit()
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            except db.IntegrityError:
                error = f"User {username} is already registered."

        flash(error, 'error')
    return render_template('register.html')

@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = database.get_db()
        error = None
        user = db.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password_hash'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('dashboard'))

        flash(error, 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    db = database.get_db()
    # Get projects where user is a member
    projects = db.execute('''
        SELECT p.*, pm.role 
        FROM projects p 
        JOIN project_members pm ON p.id = pm.project_id 
        WHERE pm.user_id = ?
        ORDER BY p.created_at DESC
    ''', (session['user_id'],)).fetchall()
    return render_template('dashboard.html', projects=projects)

@app.route('/project/new', methods=('POST',))
@login_required
def new_project():
    name = request.form['name']
    if name:
        db = database.get_db()
        cursor = db.cursor()
        cursor.execute('INSERT INTO projects (name) VALUES (?)', (name,))
        project_id = cursor.lastrowid
        # Add creator as owner
        cursor.execute(
            'INSERT INTO project_members (project_id, user_id, role) VALUES (?, ?, ?)',
            (project_id, session['user_id'], 'owner')
        )
        db.commit()
        flash('Project created.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/project/<int:project_id>')
@login_required
def view_project(project_id):
    db = database.get_db()
    # Check access
    member = db.execute(
        'SELECT role FROM project_members WHERE project_id = ? AND user_id = ?',
        (project_id, session['user_id'])
    ).fetchone()
    
    if not member:
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))

    project = db.execute('SELECT * FROM projects WHERE id = ?', (project_id,)).fetchone()
    documents = db.execute('SELECT * FROM documents WHERE project_id = ?', (project_id,)).fetchall()
    members = db.execute('''
        SELECT u.username, pm.role 
        FROM project_members pm 
        JOIN users u ON pm.user_id = u.id 
        WHERE pm.project_id = ?
    ''', (project_id,)).fetchall()

    # Get non-members for invitation
    all_users = db.execute('SELECT id, username FROM users').fetchall()
    current_member_names = [m['username'] for m in members]
    inviteable_users = [u for u in all_users if u['username'] not in current_member_names]

    return render_template('project.html', project=project, role=member['role'], documents=documents, members=members, inviteable_users=inviteable_users)

@app.route('/project/<int:project_id>/invite', methods=('POST',))
@login_required
def invite_member(project_id):
    db = database.get_db()
    member = db.execute(
        'SELECT role FROM project_members WHERE project_id = ? AND user_id = ?',
        (project_id, session['user_id'])
    ).fetchone()
    
    if not member or member['role'] != 'owner':
        flash('Only project owners can invite members.', 'error')
        return redirect(url_for('view_project', project_id=project_id))

    user_id_to_invite = request.form.get('user_id')
    role = request.form.get('role', 'viewer')
    
    if user_id_to_invite:
        try:
            db.execute(
                'INSERT INTO project_members (project_id, user_id, role) VALUES (?, ?, ?)',
                (project_id, user_id_to_invite, role)
            )
            db.commit()
            flash('Member invited successfully.', 'success')
        except db.IntegrityError:
            flash('Failed to invite member.', 'error')

    return redirect(url_for('view_project', project_id=project_id))

@app.route('/project/<int:project_id>/document/new', methods=('POST',))
@login_required
def new_document(project_id):
    db = database.get_db()
    member = db.execute(
        'SELECT role FROM project_members WHERE project_id = ? AND user_id = ?',
        (project_id, session['user_id'])
    ).fetchone()
    
    if not member or member['role'] not in ['owner', 'editor']:
        flash('You do not have permission to create documents in this project.', 'error')
        return redirect(url_for('view_project', project_id=project_id))

    title = request.form['title'].strip()
    if title:
        db.execute('INSERT INTO documents (project_id, title) VALUES (?, ?)', (project_id, title))
        db.commit()
        flash('Document created.', 'success')
    return redirect(url_for('view_project', project_id=project_id))

@app.route('/document/<int:doc_id>', methods=('GET', 'POST'))
@login_required
def document(doc_id):
    db = database.get_db()
    doc = db.execute('SELECT * FROM documents WHERE id = ?', (doc_id,)).fetchone()
    if not doc:
        return "Document not found", 404

    member = db.execute(
        'SELECT role FROM project_members WHERE project_id = ? AND user_id = ?',
        (doc['project_id'], session['user_id'])
    ).fetchone()
    
    if not member:
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))

    # Handle POST for saving content
    if request.method == 'POST':
        if member['role'] not in ['owner', 'editor']:
            flash('You do not have permission to edit this document.', 'error')
            return redirect(url_for('document', doc_id=doc_id))
            
        action = request.form.get('action')
        if action == 'lock':
            if doc['locked_by_user_id'] is None or doc['locked_by_user_id'] == session['user_id']:
                db.execute("UPDATE documents SET locked_by_user_id = ?, locked_at = CURRENT_TIMESTAMP WHERE id = ?", (session['user_id'], doc_id))
                db.commit()
            else:
                flash("Document is already locked by someone else.", "error")
        elif action == 'unlock':
            if doc['locked_by_user_id'] == session['user_id']:
                db.execute("UPDATE documents SET locked_by_user_id = NULL, locked_at = NULL WHERE id = ?", (doc_id,))
                db.commit()
        elif action == 'save':
            if doc['locked_by_user_id'] == session['user_id']:
                content = request.form.get('content')
                db.execute("UPDATE documents SET content = ?, version = version + 1, last_modified_at = CURRENT_TIMESTAMP WHERE id = ?", (content, doc_id))
                db.commit()
                flash("Saved successfully.", "success")
            else:
                flash("You must lock the document before saving.", "error")

        return redirect(url_for('document', doc_id=doc_id))

    # GET request
    locked_by_username = None
    if doc['locked_by_user_id']:
        u = db.execute('SELECT username FROM users WHERE id = ?', (doc['locked_by_user_id'],)).fetchone()
        if u:
            locked_by_username = u['username']

    can_edit = member['role'] in ['owner', 'editor']
    is_locked_by_me = doc['locked_by_user_id'] == session['user_id']
    is_locked = doc['locked_by_user_id'] is not None

    return render_template('document.html', doc=doc, can_edit=can_edit, is_locked_by_me=is_locked_by_me, is_locked=is_locked, locked_by_username=locked_by_username)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
