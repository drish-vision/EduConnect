from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder='templates', static_folder='static')

# Secret Key
app.secret_key = "your_secret_key"

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Drishya@2006'
app.config['MYSQL_DB'] = 'educonnect'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# Flask-Login Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'home'

# User Class
class User(UserMixin):
    def __init__(self, id, email, role):
        self.id = id
        self.email = email
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, email, 'student' AS role FROM students WHERE id = %s", (user_id,))
    user = cur.fetchone()
    
    if not user:
        cur.execute("SELECT id, email, 'teacher' AS role FROM teachers WHERE id = %s", (user_id,))
        user = cur.fetchone()
    
    cur.close()
    return User(user['id'], user['email'], user['role']) if user else None

# Home Page
@app.route('/')
def home():
    return render_template('educationalportal.html')

# Student Login
@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, email, password FROM students WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        
        if user and check_password_hash(user['password'], password):
            login_user(User(user['id'], user['email'], 'student'))
            flash("Login successful!", "success")
            return redirect(url_for('student_dashboard'))
        
        flash("Invalid email or password.", "danger")
    return render_template('student_login.html')

# Teacher Login
@app.route('/teacher_login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, email, password FROM teachers WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        
        if user and check_password_hash(user['password'], password):
            login_user(User(user['id'], user['email'], 'teacher'))
            flash("Login successful!", "success")
            return redirect(url_for('teacher_dashboard'))
        
        flash("Invalid email or password.", "danger")
    return render_template('teacher_login.html')

# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "info")
    return redirect(url_for('home'))

# Student Dashboard
@app.route('/student_dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('home'))
    return render_template('student_dashboard.html')

# Teacher Dashboard
@app.route('/teacher_dashboard')
@login_required
def teacher_dashboard():
    if current_user.role != 'teacher':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('home'))
    return render_template('teacher_dashboard.html')

# Upload Assignment Route
@app.route('/upload_assignment', methods=['POST'])
@login_required
def upload_assignment():
    if current_user.role != 'teacher':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('home'))
    
    title = request.form['title']
    due_date = request.form['due_date']
    
    # Here, you can insert the assignment into the database (or process it as needed)
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO assignments (teacher_id, title, due_date) VALUES (%s, %s, %s)",
                (current_user.id, title, due_date))
    mysql.connection.commit()
    cur.close()

    flash("Assignment uploaded successfully!", "success")
    return redirect(url_for('teacher_dashboard'))

# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form.get('role')
        name = request.form.get('name')
        email = request.form.get('email')
        password = generate_password_hash(request.form.get('password'))
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT email FROM students WHERE email = %s UNION SELECT email FROM teachers WHERE email = %s", (email, email))
        existing_user = cur.fetchone()
        
        if existing_user:
            flash("Email already registered. Please login.", "warning")
            return redirect(url_for('home'))
        
        if role == 'student':
            area = request.form.get('area')
            class_level = request.form.get('class')
            cur.execute("INSERT INTO students (name, email, area, class, password) VALUES (%s, %s, %s, %s, %s)",
                        (name, email, area, class_level, password))
        else:
            department = request.form.get('department')
            cur.execute("INSERT INTO teachers (name, email, department, password) VALUES (%s, %s, %s, %s)",
                        (name, email, department, password))
        
        mysql.connection.commit()
        cur.close()
        
        flash("Registration successful! Please login.", "success")
        return redirect(url_for('home'))
    return render_template('register.html')

# Run Flask App
if __name__ == '__main__':
    app.run(debug=True)
