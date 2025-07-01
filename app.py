from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from decimal import Decimal
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for session management

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',         
        password='Sushma@12',
        database='crowdconnect'         
    )

# Landing Page
@app.route('/')
def landing():
    return render_template('landing.html')

# Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user and user['password'] == password:
            session['user_id'] = user['id']
            session['is_admin'] = user['is_admin']
            return redirect(url_for('projects'))
        else:
            # handle invalid login
            pass
    return render_template('login.html')

# Projects Page
@app.route('/projects')
def projects():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM projects')
    projects = cursor.fetchall()

    # If admin, fetch donations for each project
    donations_by_project = {}
    if session.get('is_admin'):
        for project in projects:
            cursor.execute(
                "SELECT users.username, donations.amount FROM donations "
                "JOIN users ON donations.user_id = users.id "
                "WHERE donations.project_id = %s", (project['id'],)
            )
            donations_by_project[project['id']] = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'projects.html',
        projects=projects,
        donations_by_project=donations_by_project if session.get('is_admin') else None
    )

# Delete Project (Admin Only)
@app.route('/delete_project/<int:project_id>', methods=['POST'])
def delete_project(project_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return "Access denied", 403

    conn = get_db_connection()
    cursor = conn.cursor()
    # Optionally, delete related donations first if you have foreign key constraints
    cursor.execute('DELETE FROM donations WHERE project_id = %s', (project_id,))
    cursor.execute('DELETE FROM projects WHERE id = %s', (project_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('projects'))

# Donate Page
# @app.route('/donate/<int:project_id>', methods=['GET', 'POST'])
# def donate(project_id):
#     if 'user_id' not in session:
#         return redirect(url_for('login'))

#     conn = get_db_connection()
#     cursor = conn.cursor(dictionary=True)
#     cursor.execute('SELECT * FROM projects WHERE id = %s', (project_id,))
#     project = cursor.fetchone()

#     if project is None:
#         cursor.close()
#         conn.close()
#         return "Project not found!", 404

#     if request.method == 'POST':
#         print("Current user_id in session:", session.get('user_id'))  # Debug
#         donation_amount = Decimal(request.form['amount'])
#         new_current_amount = project['current_amount'] + donation_amount

#         # Insert the donation into the donations table
#         cursor.execute(
#             'INSERT INTO donations (project_id, user_id, amount) VALUES (%s, %s, %s)',
#             (project_id, session['user_id'], donation_amount)
#         )

#         # Update the current amount for the project
#         cursor.execute(
#             'UPDATE projects SET current_amount = %s WHERE id = %s',
#             (new_current_amount, project_id)
#         )

#         conn.commit()
#         cursor.close()
#         conn.close()

#         return redirect(url_for('thank_you'))

#     cursor.close()
#     conn.close()
#     return render_template('donate.html', project=project)

@app.route('/donate/<int:project_id>', methods=['GET', 'POST'])
def donate(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM projects WHERE id = %s', (project_id,))
    project = cursor.fetchone()

    if project is None:
        cursor.close()
        conn.close()
        return "Project not found!", 404

    if request.method == 'POST':
        donation_amount = request.form['amount']
        # Redirect to payment page with amount and project_id as query params
        return redirect(url_for('fake_payment', project_id=project_id, amount=donation_amount))

    cursor.close()
    conn.close()
    return render_template('donate.html', project=project)

# Thank You Page
@app.route('/thank-you')
def thank_you():
    return render_template('thank_you.html')

# Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('is_admin', None)
    return render_template('logout.html')

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        mobile = request.form['mobile']

        if password != confirm_password:
            return 'Passwords do not match!'

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (username, email, password, mobile) VALUES (%s, %s, %s, %s)',
            (username, email, password, mobile)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('login'))
    return render_template('register.html')

# About Us
@app.route('/about')
def about():
    return render_template('aboutus.html')

# Contact Us
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        print(f"Message from {name} ({email}): {message}")
        return redirect(url_for('contact'))
    return render_template('contactus.html')

@app.route('/create-project', methods=['GET', 'POST'])
def create_project():
    if 'user_id' not in session or not session.get('is_admin'):
        return "Access denied", 403  # Or redirect to another page
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        target_amount = request.form['target_amount']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO projects (title, description, target_amount, current_amount) VALUES (%s, %s, %s, %s)',
            (title, description, target_amount, 0)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('projects'))
    return render_template('create_project.html')

@app.route('/donors/<int:project_id>')
def view_donors(project_id):
    if not session.get('is_admin'):
        return "Access denied", 403

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT title FROM projects WHERE id = %s', (project_id,))
    project = cursor.fetchone()

    cursor.execute(
        "SELECT users.username, donations.amount, donations.donated_at FROM donations "
        "JOIN users ON donations.user_id = users.id "
        "WHERE donations.project_id = %s", (project_id,)
    )
    donors = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('donors.html', project=project, donors=donors)


# @app.route('/fake_payment', methods=['GET', 'POST'])
# def fake_payment():
#     project_id = request.args.get('project_id') or request.form.get('project_id')
#     amount = request.args.get('amount') or request.form.get('amount')
#     if request.method == 'POST':
#         # Save the donation after "payment"
#         if 'user_id' not in session:
#             return redirect(url_for('login'))
#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)
#         cursor.execute('SELECT * FROM projects WHERE id = %s', (project_id,))
#         project = cursor.fetchone()
#         if project is None:
#             cursor.close()
#             conn.close()
#             return "Project not found!", 404

#         donation_amount = Decimal(amount)
#         new_current_amount = project['current_amount'] + donation_amount

#         cursor.execute(
#             'INSERT INTO donations (project_id, user_id, amount) VALUES (%s, %s, %s)',
#             (project_id, session['user_id'], donation_amount)
#         )
#         cursor.execute(
#             'UPDATE projects SET current_amount = %s WHERE id = %s',
#             (new_current_amount, project_id)
#         )

#         # Automatically delete project if target is reached or exceeded
#         if new_current_amount >= project['target_amount']:
#             cursor.execute('DELETE FROM donations WHERE project_id = %s', (project_id,))
#             cursor.execute('DELETE FROM projects WHERE id = %s', (project_id,))

#         conn.commit()
#         cursor.close()
#         conn.close()

#         flash('Payment successful! Thank you for your donation.', 'success')
#         return redirect(url_for('thank_you'))

#     return render_template('payment.html', project_id=project_id, amount=amount)
@app.route('/fake_payment', methods=['GET', 'POST'])
def fake_payment():
    project_id = request.args.get('project_id') or request.form.get('project_id')
    amount = request.args.get('amount') or request.form.get('amount')
    show_otp = False

    if request.method == 'POST':
        if 'otp' not in request.form:
            # First POST: show OTP field
            show_otp = True
            return render_template('payment.html', project_id=project_id, amount=amount, show_otp=show_otp)
        else:
            # Second POST: check OTP
            otp = request.form['otp']
            if otp != '123456':  # You can set any static OTP for testing
                show_otp = True
                error = "Invalid OTP. Please try again."
                return render_template('payment.html', project_id=project_id, amount=amount, show_otp=show_otp, error=error)
            # OTP correct, process payment
            if 'user_id' not in session:
                return redirect(url_for('login'))
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT * FROM projects WHERE id = %s', (project_id,))
            project = cursor.fetchone()
            if project is None:
                cursor.close()
                conn.close()
                return "Project not found!", 404

            donation_amount = Decimal(amount)
            new_current_amount = project['current_amount'] + donation_amount

            cursor.execute(
                'INSERT INTO donations (project_id, user_id, amount) VALUES (%s, %s, %s)',
                (project_id, session['user_id'], donation_amount)
            )
            cursor.execute(
                'UPDATE projects SET current_amount = %s WHERE id = %s',
                (new_current_amount, project_id)
            )

            if new_current_amount >= project['target_amount']:
                cursor.execute('DELETE FROM donations WHERE project_id = %s', (project_id,))
                cursor.execute('DELETE FROM projects WHERE id = %s', (project_id,))

            conn.commit()
            cursor.close()
            conn.close()

            flash('Payment successful! Thank you for your donation.', 'success')
            return redirect(url_for('thank_you'))

    return render_template('payment.html', project_id=project_id, amount=amount, show_otp=show_otp)

if __name__ == '__main__':
    app.run(debug=True)
