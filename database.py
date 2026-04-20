# database.py
import sqlite3
import json
import hashlib
from datetime import datetime
import os

DB_NAME = 'hostel_booking.db'

def get_db_connection():
    """Create database connection with row factory"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize database tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Applications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            app_id INTEGER PRIMARY KEY AUTOINCREMENT,
            applicant_name TEXT NOT NULL,
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
    
    # Add new columns if they don't exist (for existing databases)
    try:
        cursor.execute("ALTER TABLE applications ADD COLUMN check_in_date TIMESTAMP")
    except:
        pass
    
    try:
        cursor.execute("ALTER TABLE applications ADD COLUMN check_out_date TIMESTAMP")
    except:
        pass
    
    try:
        cursor.execute("ALTER TABLE applications ADD COLUMN room_status TEXT DEFAULT 'Booked'")
    except:
        pass
    
    # Admin table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT,
            email TEXT
        )
    ''')
    
    # Insert default admin if not exists
    cursor.execute("SELECT * FROM admin WHERE username='admin'")
    if not cursor.fetchone():
        hashed = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute('''
            INSERT INTO admin (username, password, full_name, email)
            VALUES (?, ?, ?, ?)
        ''', ('admin', hashed, 'Administrator', 'admin@diat.ac.in'))
    
    conn.commit()
    
    # Check if we have any applications, if not add sample data
    cursor.execute("SELECT COUNT(*) as count FROM applications")
    count = cursor.fetchone()['count']
    
    if count == 0:
        print("📝 Adding sample applications...")
        add_sample_applications(conn)
    
    conn.close()
    print("✅ Database initialized successfully!")

def add_sample_applications(conn):
    """Add sample applications for testing"""
    cursor = conn.cursor()
    
    # Sample guests with adults and children
    guests1 = json.dumps([
        {'name': 'Dr. Rajesh Kumar', 'age_sex': '45/M', 'guest_type': 'Adult', 'nationality': 'Indian', 
         'aadhaar': '1234-5678-9012', 'contact': '9876543210'},
        {'name': 'Riya Kumar', 'age_sex': '10/F', 'guest_type': 'Child', 'nationality': 'Indian', 
         'aadhaar': '2345-6789-0123', 'contact': '9876543211'}
    ])
    
    guests2 = json.dumps([
        {'name': 'Prof. Suresh Verma', 'age_sex': '55/M', 'guest_type': 'Adult', 'nationality': 'Indian', 
         'aadhaar': '2345-6789-0123', 'contact': '9876543211'},
        {'name': 'Mrs. Anjali Verma', 'age_sex': '50/F', 'guest_type': 'Adult', 'nationality': 'Indian', 
         'aadhaar': '3456-7890-1234', 'contact': '9876543212'},
        {'name': 'Master Arjun Verma', 'age_sex': '8/M', 'guest_type': 'Child', 'nationality': 'Indian', 
         'aadhaar': '4567-8901-2345', 'contact': '9876543213'}
    ])
    
    guests3 = json.dumps([])  # No guests
    
    # Insert sample data
    sample_apps = [
        ('Dr. Rajesh Kumar', 'Serving DRDO', '9876543210', 'rajesh@drdo.in',
         'Research Meeting', 'Dr. Sharma', 'Urgent', guests1,
         '15-03-2026 10:00', '18-03-2026 18:00', 1, 'No', 'Self', 'Dr. Rajesh Kumar', 'Pending', 'Booked'),
        
        ('Prof. Suresh Verma', 'Retired DRDO', '9876543211', 'suresh@email.com',
         'Conference', 'Dr. Patil', 'Guest lecture', guests2,
         '20-03-2026 09:00', '22-03-2026 17:00', 2, 'Yes', 'Organization', 'Prof. Suresh Verma', 'Approved', 'Booked'),
        
        ('Ms. Priya Singh', 'Other Govt Emp.', '9876543212', 'priya@gov.in',
         'Training Program', 'Col. Mehta', '', guests3,
         '25-03-2026 14:00', '28-03-2026 11:00', 1, 'No', 'Self', 'Ms. Priya Singh', 'Pending', 'Booked')
    ]
    
    for app in sample_apps:
        cursor.execute('''
            INSERT INTO applications (
                applicant_name, applicant_type, mobile, email, purpose,
                referred_by, remarks, guest_details, from_date, to_date,
                rooms_required, messing_required, billing_person, signature, status, room_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', app)
    
    conn.commit()
    print("✅ Sample applications added!")

def insert_application(form_data, guest_list):
    """Insert new application"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO applications (
            applicant_name, designation, applicant_type, mobile, email,
            purpose, referred_by, remarks, guest_details, from_date,
            to_date, rooms_required, messing_required, billing_person, signature
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        form_data.get('applicant_name', ''),
        form_data.get('designation', ''),
        form_data.get('applicant_type', ''),
        form_data.get('mobile', ''),
        form_data.get('email', ''),
        form_data.get('purpose', ''),
        form_data.get('referred_by', ''),
        form_data.get('remarks', ''),
        json.dumps(guest_list),
        form_data.get('from_date', ''),
        form_data.get('to_date', ''),
        int(form_data.get('rooms_required', 1)),
        form_data.get('messing_required', 'No'),
        form_data.get('billing_person', ''),
        form_data.get('signature', '')
    ))
    
    app_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return app_id

def get_all_applications():
    """Get all applications with guest count"""
    conn = get_db_connection()
    
    try:
        applications = conn.execute('''
            SELECT 
                app_id,
                applicant_name,
                mobile,
                from_date,
                to_date,
                rooms_required,
                status,
                submitted_date,
                guest_details,
                room_status,
                check_in_date,
                check_out_date
            FROM applications 
            ORDER BY submitted_date DESC
        ''').fetchall()
        
        # Convert to list of dictionaries with guest count
        result = []
        for app in applications:
            # Calculate guest counts from guest_details JSON
            guest_count = 0
            adult_count = 0
            child_count = 0
            
            if app['guest_details']:
                try:
                    guests = json.loads(app['guest_details'])
                    guest_count = len(guests)
                    adult_count = len([g for g in guests if g.get('guest_type') == 'Adult'])
                    child_count = len([g for g in guests if g.get('guest_type') == 'Child'])
                except:
                    guest_count = 0
            
            result.append({
                'app_id': app['app_id'],
                'applicant_name': app['applicant_name'] or 'N/A',
                'mobile': app['mobile'] or 'N/A',
                'from_date': app['from_date'] or 'N/A',
                'to_date': app['to_date'] or 'N/A',
                'rooms_required': app['rooms_required'] or 1,
                'status': app['status'] or 'Pending',
                'submitted_date': app['submitted_date'] or '',
                'guest_count': guest_count,
                'adult_count': adult_count,
                'child_count': child_count,
                'room_status': app['room_status'] or 'Booked',
                'check_in_date': app['check_in_date'],
                'check_out_date': app['check_out_date']
            })
        
        return result
        
    except Exception as e:
        print(f"❌ Error in get_all_applications: {e}")
        return []
    
    finally:
        conn.close()

def get_pending_applications():
    """Get pending applications"""
    conn = get_db_connection()
    applications = conn.execute('''
        SELECT * FROM applications 
        WHERE status='Pending' 
        ORDER BY submitted_date
    ''').fetchall()
    conn.close()
    return applications

def get_application_by_id(app_id):
    """Get single application"""
    conn = get_db_connection()
    application = conn.execute('''
        SELECT * FROM applications WHERE app_id = ?
    ''', (app_id,)).fetchone()
    conn.close()
    
    if application:
        return dict(application)
    return None

def update_application_status(app_id, status, approved_by='Admin'):
    """Update application status"""
    conn = get_db_connection()
    conn.execute('''
        UPDATE applications 
        SET status=?, approved_by=?, approved_date=CURRENT_TIMESTAMP
        WHERE app_id=?
    ''', (status, approved_by, app_id))
    conn.commit()
    conn.close()

def delete_application(app_id):
    """Delete application"""
    conn = get_db_connection()
    conn.execute('DELETE FROM applications WHERE app_id=?', (app_id,))
    conn.commit()
    conn.close()

def verify_admin(username, password):
    """Verify admin credentials"""
    conn = get_db_connection()
    hashed = hashlib.sha256(password.encode()).hexdigest()
    admin = conn.execute('''
        SELECT * FROM admin WHERE username=? AND password=?
    ''', (username, hashed)).fetchone()
    conn.close()
    return admin is not None

# ==================== CHECK-IN / CHECK-OUT FUNCTIONS ====================

def check_in_application(app_id, admin_name):
    """Check-in application - Guest arrives"""
    conn = get_db_connection()
    
    # Check if already checked in
    current = conn.execute('''
        SELECT room_status FROM applications WHERE app_id = ?
    ''', (app_id,)).fetchone()
    
    if current and current['room_status'] == 'Occupied':
        conn.close()
        return False, "Already checked in!"
    
    conn.execute('''
        UPDATE applications 
        SET check_in_date = CURRENT_TIMESTAMP,
            room_status = 'Occupied'
        WHERE app_id = ?
    ''', (app_id,))
    conn.commit()
    conn.close()
    return True, "Checked in successfully!"

def check_out_application(app_id):
    """Check-out application - Guest leaves, room becomes vacant"""
    conn = get_db_connection()
    
    # Check if already checked out
    current = conn.execute('''
        SELECT room_status FROM applications WHERE app_id = ?
    ''', (app_id,)).fetchone()
    
    if current and current['room_status'] == 'Vacant':
        conn.close()
        return False, "Already checked out!"
    
    conn.execute('''
        UPDATE applications 
        SET check_out_date = CURRENT_TIMESTAMP,
            room_status = 'Vacant'
        WHERE app_id = ?
    ''', (app_id,))
    conn.commit()
    conn.close()
    return True, "Checked out successfully! Room is now vacant."

def get_current_occupancy():
    """Get currently occupied rooms"""
    conn = get_db_connection()
    occupied_rooms = conn.execute('''
        SELECT * FROM applications 
        WHERE room_status = 'Occupied'
        AND check_out_date IS NULL
        ORDER BY check_in_date DESC
    ''').fetchall()
    conn.close()
    
    result = []
    for room in occupied_rooms:
        result.append(dict(room))
    return result

def get_room_status_count():
    """Get count of rooms by status based on total rooms"""
    conn = get_db_connection()
    
    # Total rooms fixed
    TOTAL_ROOMS = 250
    
    # Occupied rooms (rooms with guests inside) - sum of rooms_required
    occupied = conn.execute('''
        SELECT SUM(rooms_required) as count FROM applications 
        WHERE room_status = 'Occupied'
    ''').fetchone()['count'] or 0
    
    # Booked rooms (approved but not checked in) - sum of rooms_required
    booked = conn.execute('''
        SELECT SUM(rooms_required) as count FROM applications 
        WHERE status = 'Approved' 
        AND (room_status = 'Booked' OR room_status IS NULL)
    ''').fetchone()['count'] or 0
    
    # Vacant rooms = Total rooms - (Occupied + Booked)
    vacant = TOTAL_ROOMS - (occupied + booked)
    
    conn.close()
    return {
        'occupied': occupied,
        'booked': booked,
        'vacant': vacant
    }