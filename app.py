# app.py
import os
import sys
print(f"🐍 Python version: {sys.version}")

from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import json
from datetime import datetime
import threading
import csv

# 🔴 Detect database type
USE_POSTGRES = os.environ.get('DATABASE_URL') is not None

# 🔴 TRY TO IMPORT PANDAS, BUT HANDLE ERROR
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
    print("✅ Pandas available")
except ImportError:
    PANDAS_AVAILABLE = False
    print("⚠️ Pandas not available, using fallback")

app = Flask(__name__)
app.secret_key = 'hmc-hostel-secret-key-2026'

# 🔴 Database path function (for SQLite fallback)
def get_db_path():
    """Get database path - works on Railway, Render, and local"""
    if USE_POSTGRES:
        return None
    elif os.environ.get('RAILWAY_VOLUME_MOUNT_PATH'):
        db_dir = '/app/data'
        os.makedirs(db_dir, exist_ok=True)
        return os.path.join(db_dir, 'hostel_booking.db')
    elif os.environ.get('RENDER'):
        return '/tmp/hostel_booking.db'
    else:
        return 'hostel_booking.db'

# 🔴 Get CSV file path
def get_csv_path():
    """Get CSV file path for exports"""
    if USE_POSTGRES:
        return 'hostel_data.csv'
    elif os.environ.get('RAILWAY_VOLUME_MOUNT_PATH'):
        db_dir = '/app/data'
        os.makedirs(db_dir, exist_ok=True)
        return os.path.join(db_dir, 'hostel_data.csv')
    elif os.environ.get('RENDER'):
        return '/tmp/hostel_data.csv'
    else:
        return os.path.join(os.getcwd(), 'hostel_data.csv')

# 🔴 Database initialization - FORCE CREATE TABLES
def ensure_database():
    """Ensure database and admin table exist"""
    if USE_POSTGRES:
        print("📁 Using PostgreSQL database - forcing table creation")
        # 🔴 FORCE INITIALIZE ALL TABLES
        from database import init_database
        init_database()
        print("✅ PostgreSQL tables created")
        
        # Also ensure admin table separately
        try:
            from database import ensure_admin_table
            ensure_admin_table()
            print("✅ Admin table ensured")
        except:
            pass
            
    else:
        db_path = get_db_path()
        print(f"📁 Ensuring SQLite database at: {db_path}")
        
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            print(f"📁 Created directory: {db_dir}")
        
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                app_id INTEGER PRIMARY KEY AUTOINCREMENT,
                applicant_name TEXT,
                designation TEXT,
                applicant_type TEXT,
                mobile TEXT,
                email TEXT,
                purpose TEXT,
                referred_by TEXT,
                remarks TEXT,
                guest_details TEXT DEFAULT '[]',
                from_date TEXT,
                to_date TEXT,
                rooms_required INTEGER DEFAULT 1,
                messing_required TEXT DEFAULT 'No',
                billing_person TEXT,
                signature TEXT,
                status TEXT DEFAULT 'Pending',
                submitted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_by TEXT,
                approved_date TIMESTAMP,
                check_in_date TIMESTAMP,
                check_out_date TIMESTAMP,
                room_status TEXT DEFAULT 'Booked'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin (
                admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT,
                email TEXT
            )
        ''')
        
        import hashlib
        hashed = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute("SELECT * FROM admin WHERE username='admin'")
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO admin (username, password, full_name, email)
                VALUES (?, ?, ?, ?)
            ''', ('admin', hashed, 'Administrator', 'admin@diat.ac.in'))
            print("✅ Default admin user created")
        
        conn.commit()
        conn.close()
        print("✅ SQLite database ensured")

# 🔴 Call this BEFORE importing database module
ensure_database()

# Now import database module
from database import *
import database

# Update database module path for SQLite fallback
if not USE_POSTGRES:
    database.DB_NAME = get_db_path()

# ==================== HELPER FUNCTION ====================
def update_csv():
    """Auto update CSV file with latest database data"""
    try:
        filepath = get_csv_path()
        print(f"📁 CSV path: {filepath}")
        
        conn = get_db_connection()
        
        if USE_POSTGRES:
            import psycopg2.extras
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("SELECT * FROM applications ORDER BY submitted_date DESC")
            rows = cursor.fetchall()
            data = [dict(row) for row in rows]
            
            if PANDAS_AVAILABLE and data:
                df = pd.DataFrame(data)
                def get_guest_count(guest_details):
                    try:
                        if guest_details and guest_details != '[]':
                            guests = json.loads(guest_details)
                            return len(guests)
                        return 0
                    except:
                        return 0
                if 'guest_details' in df.columns:
                    df['guest_count'] = df['guest_details'].apply(get_guest_count)
                df.to_csv(filepath, index=False)
            else:
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    if data:
                        writer = csv.DictWriter(f, fieldnames=data[0].keys())
                        writer.writeheader()
                        writer.writerows(data)
            
            conn.close()
            print(f"✅ CSV Auto-Updated! Total records: {len(data)}")
            return len(data)
            
        else:
            import sqlite3
            conn = sqlite3.connect(get_db_path())
            
            if PANDAS_AVAILABLE:
                df = pd.read_sql_query("SELECT * FROM applications ORDER BY submitted_date DESC", conn)
                def get_guest_count(guest_details):
                    try:
                        if guest_details and guest_details != '[]':
                            guests = json.loads(guest_details)
                            return len(guests)
                        return 0
                    except:
                        return 0
                df['guest_count'] = df['guest_details'].apply(get_guest_count)
                conn.close()
                df.to_csv(filepath, index=False)
                print(f"✅ CSV Auto-Updated! Total records: {len(df)}")
                return len(df)
            else:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM applications ORDER BY submitted_date DESC")
                rows = cursor.fetchall()
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([i[0] for i in cursor.description])
                    writer.writerows(rows)
                conn.close()
                print(f"✅ CSV Auto-Updated! Total records: {len(rows)}")
                return len(rows)
            
    except Exception as e:
        print(f"⚠️ CSV update failed: {e}")
        return 0

def send_email_async(application, email_type='approval'):
    try:
        from email_service import send_approval_email, send_rejection_email
        if email_type == 'approval':
            send_approval_email(application)
        elif email_type == 'rejection':
            send_rejection_email(application)
    except Exception as e:
        print(f"⚠️ Email error: {e}")

# ==================== MAIN ROUTES ====================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/student-form')
def student_form():
    return render_template('student_form.html', today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/submit-application', methods=['POST'])
def submit_application():
    try:
        form_data = request.form.to_dict()
        
        if form_data.get('applicant_type') == 'Others':
            other_text = request.form.get('other_applicant_type', '')
            if other_text:
                form_data['applicant_type'] = f"Others - {other_text}"
        
        total_guests = int(request.form.get('total_guests', 0))
        if total_guests > 4:
            total_guests = 4
        
        guest_list = []
        for i in range(1, total_guests + 1):
            name = request.form.get(f'guest_name_{i}')
            if name and name.strip():
                guest = {
                    'name': name,
                    'age_sex': request.form.get(f'guest_age_sex_{i}', ''),
                    'guest_type': request.form.get(f'guest_type_{i}', 'Adult'),
                    'nationality': request.form.get(f'guest_nationality_{i}', ''),
                    'aadhaar': request.form.get(f'guest_aadhaar_{i}', ''),
                    'contact': request.form.get(f'guest_contact_{i}', '')
                }
                guest_list.append(guest)
        
        app_id = insert_application(form_data, guest_list)
        update_csv()
        
        flash(f'✅ Application submitted successfully! Application ID: {app_id}', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        flash(f'❌ Error submitting application: {str(e)}', 'error')
        return redirect(url_for('student_form'))

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if verify_admin(username, password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('✅ Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('❌ Invalid username or password!', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin-dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('admin_login'))
    
    applications = get_all_applications()
    
    print(f"\n{'='*50}")
    print(f"📊 Admin Dashboard - Found {len(applications)} applications")
    for app in applications:
        print(f"   ID: {app['app_id']} | Name: {app['applicant_name']} | Status: {app['status']} | Room: {app.get('room_status', 'Booked')}")
    print(f"{'='*50}\n")
    
    total = len(applications)
    pending = len([a for a in applications if a['status'] == 'Pending'])
    approved = len([a for a in applications if a['status'] == 'Approved'])
    rejected = len([a for a in applications if a['status'] == 'Rejected'])
    room_stats = get_room_status_count()
    
    return render_template('admin_dashboard.html', 
                         applications=applications,
                         total=total,
                         pending=pending,
                         approved=approved,
                         rejected=rejected,
                         room_stats=room_stats)

@app.route('/view-application/<int:app_id>')
def view_application(app_id):
    if not session.get('admin_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('admin_login'))
    
    application = get_application_by_id(app_id)
    if not application:
        flash('Application not found!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    guest_details = []
    if application.get('guest_details'):
        try:
            guest_details = json.loads(application['guest_details'])
        except:
            guest_details = []
    
    return render_template('view_application.html', 
                         application=application,
                         guest_details=guest_details)

@app.route('/approve-application/<int:app_id>')
def approve_application(app_id):
    if not session.get('admin_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('admin_login'))
    
    update_application_status(app_id, 'Approved', session['admin_username'])
    
    application = get_application_by_id(app_id)
    if application and application.get('email'):
        try:
            email_thread = threading.Thread(target=send_email_async, args=(application, 'approval'))
            email_thread.start()
        except:
            pass
    
    update_csv()
    flash(f'✅ Application #{app_id} approved successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/reject-application/<int:app_id>')
def reject_application(app_id):
    if not session.get('admin_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('admin_login'))
    
    update_application_status(app_id, 'Rejected', session['admin_username'])
    update_csv()
    flash(f'⚠️ Application #{app_id} rejected!', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/delete-application/<int:app_id>')
def delete_application_route(app_id):
    if not session.get('admin_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('admin_login'))
    
    delete_application(app_id)
    update_csv()
    flash(f'🗑️ Application #{app_id} deleted!', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin-logout')
def admin_logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/check-in/<int:app_id>')
def check_in(app_id):
    if not session.get('admin_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('admin_login'))
    
    success, message = check_in_application(app_id, session['admin_username'])
    if success:
        update_csv()
        flash(f'🚪 {message} Room is now OCCUPIED.', 'success')
    else:
        flash(f'❌ {message}', 'error')
    return redirect(url_for('admin_dashboard'))

@app.route('/check-out/<int:app_id>')
def check_out(app_id):
    if not session.get('admin_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('admin_login'))
    
    success, message = check_out_application(app_id)
    if success:
        update_csv()
        flash(f'🚪 {message} Room is now VACANT.', 'success')
    else:
        flash(f'❌ {message}', 'error')
    return redirect(url_for('admin_dashboard'))

@app.route('/current-occupancy')
def current_occupancy():
    if not session.get('admin_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('admin_login'))
    
    occupied_rooms = get_current_occupancy()
    room_stats = get_room_status_count()
    applications = get_all_applications()
    
    return render_template('current_occupancy.html', 
                         occupied_rooms=occupied_rooms,
                         room_stats=room_stats,
                         applications=applications)

@app.route('/export-csv')
def export_csv():
    try:
        filepath = get_csv_path()
        update_csv()
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>CSV Export - HMC Hostel</title>
            <style>
                body {{ font-family: Arial; text-align: center; padding: 50px; background: #f5f6fa; }}
                .success {{ background: #d4edda; color: #155724; padding: 20px; border-radius: 10px; }}
                .btn {{ background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="success">
                <h2>✅ CSV Export Successful!</h2>
                <p><strong>File:</strong> {filepath}</p>
                <a href="/download-csv" class="btn" style="background: #27ae60;">📥 Download CSV</a>
            </div>
            <a href="/admin-dashboard" class="btn">← Back to Dashboard</a>
            <a href="/" class="btn" style="background: #27ae60;">🏠 Home</a>
        </body>
        </html>
        """
    except Exception as e:
        return f"<h2>❌ CSV Export Failed</h2><p>Error: {str(e)}</p>"

@app.route('/download-csv')
def download_csv():
    try:
        filepath = get_csv_path()
        update_csv()
        return send_file(filepath, as_attachment=True, download_name='hostel_data.csv')
    except Exception as e:
        return f"Error: {e}"

@app.route('/add-bulk-data')
def add_bulk_data():
    if not session.get('admin_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('admin_login'))
    
    try:
        import random
        
        names = ['Dr. Rajesh Kumar', 'Prof. Suresh Verma', 'Ms. Priya Singh', 'Dr. Anjali Sharma']
        types = ['Serving DRDO', 'Retired DRDO', 'Other Govt Emp.', 'Others']
        purposes = ['Research Meeting', 'Conference', 'Training Program', 'Workshop', 'Seminar']
        
        conn = get_db_connection()
        count = 0
        
        for i in range(10):
            status = 'Approved' if i < 5 else ('Pending' if i < 8 else 'Rejected')
            
            if USE_POSTGRES:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO applications (
                        applicant_name, applicant_type, mobile, email, purpose,
                        from_date, to_date, rooms_required, messing_required, status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    random.choice(names),
                    random.choice(types),
                    f'98{random.randint(10000000, 99999999)}',
                    f'user{i}@drdo.in',
                    random.choice(purposes),
                    f'{random.randint(1,28)}-04-2026 10:00',
                    f'{random.randint(1,28)}-04-2026 17:00',
                    random.choice([1, 2, 3]),
                    random.choice(['Yes', 'No']),
                    status
                ))
            else:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO applications (
                        applicant_name, applicant_type, mobile, email, purpose,
                        from_date, to_date, rooms_required, messing_required, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    random.choice(names),
                    random.choice(types),
                    f'98{random.randint(10000000, 99999999)}',
                    f'user{i}@drdo.in',
                    random.choice(purposes),
                    f'{random.randint(1,28)}-04-2026 10:00',
                    f'{random.randint(1,28)}-04-2026 17:00',
                    random.choice([1, 2, 3]),
                    random.choice(['Yes', 'No']),
                    status
                ))
            count += 1
        
        conn.commit()
        conn.close()
        update_csv()
        
        flash(f'✅ Added {count} sample applications!', 'success')
        
    except Exception as e:
        flash(f'❌ Error: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("🚀 HMC Hostel Booking System Starting...")
    print(f"📍 URL: http://0.0.0.0:{port}")
    print("👑 Admin: admin / admin123")
    if USE_POSTGRES:
        print("🐘 Using PostgreSQL database (data persists on restart)")
    else:
        print("🗄️ Using SQLite database")
    print("="*50)
    app.run(debug=False, host='0.0.0.0', port=port)