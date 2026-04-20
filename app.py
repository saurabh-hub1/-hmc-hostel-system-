# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import *
import json
from datetime import datetime
import os
import sqlite3
import pandas as pd
import threading

app = Flask(__name__)
app.secret_key = 'hmc-hostel-secret-key-2026'

# Initialize database on startup
init_database()

# ==================== HELPER FUNCTION ====================
def update_csv():
    """Auto update CSV file with latest database data"""
    try:
        conn = sqlite3.connect('hostel_booking.db')
        df = pd.read_sql_query("SELECT * FROM applications ORDER BY submitted_date DESC", conn)
        
        # Guest count calculate karo
        def get_guest_count(guest_details):
            try:
                if guest_details and guest_details != '[]':
                    guests = json.loads(guest_details)
                    return len(guests)
                return 0
            except:
                return 0
        
        def get_adult_count(guest_details):
            try:
                if guest_details and guest_details != '[]':
                    guests = json.loads(guest_details)
                    return len([g for g in guests if g.get('guest_type') == 'Adult'])
                return 0
            except:
                return 0
        
        def get_child_count(guest_details):
            try:
                if guest_details and guest_details != '[]':
                    guests = json.loads(guest_details)
                    return len([g for g in guests if g.get('guest_type') == 'Child'])
                return 0
            except:
                return 0
        
        df['guest_count'] = df['guest_details'].apply(get_guest_count)
        df['adult_count'] = df['guest_details'].apply(get_adult_count)
        df['child_count'] = df['guest_details'].apply(get_child_count)
        conn.close()
        
        filepath = os.path.join(os.getcwd(), 'hostel_data.csv')
        df.to_csv(filepath, index=False)
        print(f"✅ CSV Auto-Updated! Total records: {len(df)}")
        return len(df)
    except Exception as e:
        print(f"⚠️ CSV update failed: {e}")
        return 0

def send_email_async(application, email_type='approval'):
    """Send email in background thread"""
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
    """Home page with Student Form and Admin Login buttons"""
    return render_template('index.html')

@app.route('/student-form')
def student_form():
    """Display the application form"""
    return render_template('student_form.html', today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/submit-application', methods=['POST'])
def submit_application():
    """Handle form submission"""
    try:
        # Get form data
        form_data = request.form.to_dict()
        
        # Handle "Others" option
        if form_data.get('applicant_type') == 'Others':
            other_text = request.form.get('other_applicant_type', '')
            if other_text:
                form_data['applicant_type'] = f"Others - {other_text}"
        
        # Get total guests count (max 4)
        total_guests = int(request.form.get('total_guests', 0))
        if total_guests > 4:
            total_guests = 4
        
        # Collect guest details (up to 4 guests)
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
        
        # Insert into database
        app_id = insert_application(form_data, guest_list)
        
        # AUTO CSV UPDATE
        update_csv()
        
        flash(f'✅ Application submitted successfully! Application ID: {app_id}', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        flash(f'❌ Error submitting application: {str(e)}', 'error')
        return redirect(url_for('student_form'))

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
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
    """Admin dashboard showing all applications"""
    if not session.get('admin_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('admin_login'))
    
    applications = get_all_applications()
    
    # Debug print
    print(f"\n{'='*50}")
    print(f"📊 Admin Dashboard - Found {len(applications)} applications")
    for app in applications:
        print(f"   ID: {app['app_id']} | Name: {app['applicant_name']} | Status: {app['status']} | Room: {app.get('room_status', 'Booked')}")
    print(f"{'='*50}\n")
    
    # Calculate counts
    total = len(applications)
    pending = len([a for a in applications if a['status'] == 'Pending'])
    approved = len([a for a in applications if a['status'] == 'Approved'])
    rejected = len([a for a in applications if a['status'] == 'Rejected'])
    
    # Get room status counts
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
    """View single application details"""
    if not session.get('admin_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('admin_login'))
    
    application = get_application_by_id(app_id)
    if not application:
        flash('Application not found!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    # Parse guest details
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
    """Approve application"""
    if not session.get('admin_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('admin_login'))
    
    update_application_status(app_id, 'Approved', session['admin_username'])
    
    # 🔴 Send email notification in background 🔴
    application = get_application_by_id(app_id)
    if application and application.get('email'):
        try:
            email_thread = threading.Thread(target=send_email_async, args=(application, 'approval'))
            email_thread.start()
            email_sent = True
        except Exception as e:
            print(f"⚠️ Email thread error: {e}")
            email_sent = False
    else:
        email_sent = False
    
    update_csv()
    
    if email_sent:
        flash(f'✅ Application #{app_id} approved successfully! Email sent to {application.get("email")}', 'success')
    else:
        flash(f'✅ Application #{app_id} approved successfully! (Email could not be sent)', 'warning')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/reject-application/<int:app_id>')
def reject_application(app_id):
    """Reject application"""
    if not session.get('admin_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('admin_login'))
    
    update_application_status(app_id, 'Rejected', session['admin_username'])
    
    # 🔴 Send rejection email in background 🔴
    application = get_application_by_id(app_id)
    if application and application.get('email'):
        try:
            email_thread = threading.Thread(target=send_email_async, args=(application, 'rejection'))
            email_thread.start()
            email_sent = True
        except Exception as e:
            print(f"⚠️ Email thread error: {e}")
            email_sent = False
    else:
        email_sent = False
    
    update_csv()
    
    if email_sent:
        flash(f'⚠️ Application #{app_id} rejected! Email sent to {application.get("email")}', 'info')
    else:
        flash(f'⚠️ Application #{app_id} rejected! (Email could not be sent)', 'warning')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/delete-application/<int:app_id>')
def delete_application_route(app_id):
    """Delete application"""
    if not session.get('admin_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('admin_login'))
    
    delete_application(app_id)
    update_csv()
    
    flash(f'🗑️ Application #{app_id} deleted!', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin-logout')
def admin_logout():
    """Logout admin"""
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

# ==================== CHECK-IN / CHECK-OUT ROUTES ====================

@app.route('/check-in/<int:app_id>')
def check_in(app_id):
    """Check-in application - Guest arrives"""
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
    """Check-out application - Guest leaves"""
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
    """Show current occupancy"""
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

# ==================== EXPORT CSV ====================

@app.route('/export-csv')
def export_csv():
    """Manual CSV export with status page"""
    try:
        conn = sqlite3.connect('hostel_booking.db')
        df = pd.read_sql_query("SELECT * FROM applications ORDER BY submitted_date DESC", conn)
        
        def get_guest_count(guest_details):
            try:
                if guest_details and guest_details != '[]':
                    guests = json.loads(guest_details)
                    return len(guests)
                return 0
            except:
                return 0
        
        def get_adult_count(guest_details):
            try:
                if guest_details and guest_details != '[]':
                    guests = json.loads(guest_details)
                    return len([g for g in guests if g.get('guest_type') == 'Adult'])
                return 0
            except:
                return 0
        
        def get_child_count(guest_details):
            try:
                if guest_details and guest_details != '[]':
                    guests = json.loads(guest_details)
                    return len([g for g in guests if g.get('guest_type') == 'Child'])
                return 0
            except:
                return 0
        
        df['guest_count'] = df['guest_details'].apply(get_guest_count)
        df['adult_count'] = df['guest_details'].apply(get_adult_count)
        df['child_count'] = df['guest_details'].apply(get_child_count)
        conn.close()
        
        filepath = os.path.join(os.getcwd(), 'hostel_data.csv')
        df.to_csv(filepath, index=False)
        
        status_counts = df.groupby('status').size().reset_index(name='count')
        status_html = "<br>".join([f"{row['status']}: {row['count']}" for _, row in status_counts.iterrows()])
        
        room_counts = df.groupby('room_status').size().reset_index(name='count')
        room_html = "<br>".join([f"{row['room_status']}: {row['count']}" for _, row in room_counts.iterrows()])
        
        total_guests = df['guest_count'].sum()
        total_adults = df['adult_count'].sum()
        total_children = df['child_count'].sum()
        total_rooms = df['rooms_required'].sum()
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>CSV Export - HMC Hostel</title>
            <style>
                body {{ font-family: Arial; text-align: center; padding: 50px; background: #f5f6fa; }}
                .success {{ background: #d4edda; color: #155724; padding: 20px; border-radius: 10px; }}
                .stats {{ background: white; padding: 20px; margin: 20px; border-radius: 10px; }}
                .btn {{ background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="success">
                <h2>✅ CSV Export Successful!</h2>
                <p><strong>File:</strong> {filepath}</p>
                <p><strong>Total Records:</strong> {len(df)}</p>
                <p><strong>👥 Total Guests:</strong> {total_guests} (Adults: {total_adults}, Children: {total_children})</p>
                <p><strong>🏠 Total Rooms Booked:</strong> {total_rooms}</p>
            </div>
            <div class="stats">
                <h3>📊 Status Summary</h3>
                {status_html}
                <h3>🏨 Room Status Summary</h3>
                {room_html}
            </div>
            <a href="/admin-dashboard" class="btn">← Back to Dashboard</a>
            <a href="/" class="btn" style="background: #27ae60;">🏠 Home</a>
        </body>
        </html>
        """
    except Exception as e:
        return f"""
        <h2>❌ CSV Export Failed</h2>
        <p>Error: {str(e)}</p>
        <a href="/admin-dashboard">← Back to Dashboard</a>
        """

# ==================== BULK DATA ADD ====================

@app.route('/add-bulk-data')
def add_bulk_data():
    """Add 20 sample applications for demo"""
    if not session.get('admin_logged_in'):
        flash('Please login first!', 'error')
        return redirect(url_for('admin_login'))
    
    try:
        import random
        
        names = [
            'Dr. Rajesh Kumar', 'Prof. Suresh Verma', 'Ms. Priya Singh', 'Dr. Anjali Sharma',
            'Col. Amit Mehta', 'Mrs. Neha Gupta', 'Dr. Vikram Rathore', 'Prof. Sunita Desai',
            'Mr. Rahul Nair', 'Dr. Pooja Joshi', 'Maj. Sanjay Patil', 'Ms. Divya Reddy',
            'Dr. Manoj Tiwari', 'Prof. Ritu Agarwal', 'Mr. Alok Srivastava', 'Dr. Kavita Nair'
        ]
        types = ['Serving DRDO', 'Retired DRDO', 'Serving (Trl Services)', 'Other Govt Emp.', 'Others']
        purposes = ['Research Meeting', 'Conference', 'Training Program', 'Workshop', 'Seminar']
        
        conn = sqlite3.connect('hostel_booking.db')
        cursor = conn.cursor()
        
        count = 0
        for i in range(20):
            status = 'Approved' if i < 10 else ('Pending' if i < 15 else 'Rejected')
            room_status = random.choice(['Booked', 'Occupied', 'Vacant']) if status == 'Approved' else 'Booked'
            
            # Create sample guest details with adults and children
            guest_count = random.randint(0, 4)
            guests = []
            for g in range(guest_count):
                guest_type = 'Adult' if g < 2 else 'Child'
                guests.append({
                    'name': f'Guest {g+1}',
                    'age_sex': f'{random.randint(5, 60)}/{random.choice(["M", "F"])}',
                    'guest_type': guest_type,
                    'nationality': 'Indian',
                    'aadhaar': f'{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}',
                    'contact': f'98{random.randint(10000000, 99999999)}'
                })
            
            cursor.execute('''
                INSERT INTO applications (
                    applicant_name, applicant_type, mobile, email, purpose,
                    from_date, to_date, rooms_required, messing_required, 
                    status, room_status, guest_details
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                random.choice(names),
                random.choice(types),
                f'98{random.randint(10000000, 99999999)}',
                f'user{i}@drdo.in',
                random.choice(purposes),
                f'{random.randint(1,28)}-03-2026 10:00',
                f'{random.randint(1,28)}-03-2026 17:00',
                random.choice([1, 2, 3]),
                random.choice(['Yes', 'No']),
                status,
                room_status,
                json.dumps(guests)
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
    print("🚀 HMC Hostel Booking System Starting...")
    print("📍 URL: http://localhost:5000")
    print("👑 Admin: admin / admin123")
    print("="*50)
    app.run(debug=True, host='0.0.0.0', port=5000)