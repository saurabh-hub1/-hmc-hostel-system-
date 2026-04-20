# database.py
import os
import json
import hashlib
from datetime import datetime

# 🔴 Detect which database to use
USE_POSTGRES = os.environ.get('DATABASE_URL') is not None

if USE_POSTGRES:
    import psycopg2
    import psycopg2.extras
    print("✅ Using PostgreSQL database")
else:
    import sqlite3
    print("⚠️ Using SQLite database (local)")

# ==================== DATABASE PATH/URL ====================

def get_db_connection():
    """Get database connection (PostgreSQL or SQLite)"""
    if USE_POSTGRES:
        # PostgreSQL connection
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        return conn
    else:
        # SQLite connection
        if os.environ.get('RENDER'):
            db_path = '/tmp/hostel_booking.db'
        else:
            db_path = 'hostel_booking.db'
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

def get_cursor(conn):
    """Get cursor (handles both PostgreSQL and SQLite)"""
    if USE_POSTGRES:
        return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        return conn.cursor()

# ==================== DATABASE INITIALIZATION ====================

def init_database():
    """Initialize database tables (PostgreSQL or SQLite)"""
    conn = get_db_connection()
    
    if USE_POSTGRES:
        cursor = conn.cursor()
        
        # Applications table (PostgreSQL)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                app_id SERIAL PRIMARY KEY,
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
        
        # Admin table (PostgreSQL)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin (
                admin_id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT,
                email TEXT
            )
        ''')
        
        # Insert default admin
        hashed = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute("SELECT * FROM admin WHERE username='admin'")
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO admin (username, password, full_name, email)
                VALUES (%s, %s, %s, %s)
            ''', ('admin', hashed, 'Administrator', 'admin@diat.ac.in'))
            print("✅ Default admin user created")
        
        conn.commit()
        
    else:
        # SQLite version
        cursor = conn.cursor()
        
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
        
        # Add missing columns for SQLite
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
        
        # Admin table (SQLite)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin (
                admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT,
                email TEXT
            )
        ''')
        
        # Insert default admin
        hashed = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute("SELECT * FROM admin WHERE username='admin'")
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO admin (username, password, full_name, email)
                VALUES (?, ?, ?, ?)
            ''', ('admin', hashed, 'Administrator', 'admin@diat.ac.in'))
            print("✅ Default admin user created")
        
        conn.commit()
        
        # Check if we have any applications
        cursor.execute("SELECT COUNT(*) as count FROM applications")
        count = cursor.fetchone()['count']
        if count == 0:
            print("📝 Adding sample applications...")
            add_sample_applications(conn)
    
    conn.close()
    print("✅ Database initialized successfully")

def add_sample_applications(conn):
    """Add sample applications for testing"""
    if USE_POSTGRES:
        cursor = conn.cursor()
    else:
        cursor = conn.cursor()
    
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
    
    guests3 = json.dumps([])
    
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
        if USE_POSTGRES:
            cursor.execute('''
                INSERT INTO applications (
                    applicant_name, applicant_type, mobile, email, purpose,
                    referred_by, remarks, guest_details, from_date, to_date,
                    rooms_required, messing_required, billing_person, signature, status, room_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', app)
        else:
            cursor.execute('''
                INSERT INTO applications (
                    applicant_name, applicant_type, mobile, email, purpose,
                    referred_by, remarks, guest_details, from_date, to_date,
                    rooms_required, messing_required, billing_person, signature, status, room_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', app)
    
    conn.commit()
    print("✅ Sample applications added!")

# ==================== CRUD OPERATIONS ====================

def insert_application(form_data, guest_list):
    """Insert new application"""
    conn = get_db_connection()
    
    if USE_POSTGRES:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO applications (
                applicant_name, designation, applicant_type, mobile, email,
                purpose, referred_by, remarks, guest_details, from_date,
                to_date, rooms_required, messing_required, billing_person, signature
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING app_id
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
        app_id = cursor.fetchone()[0]
    else:
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
    
    if USE_POSTGRES:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('''
            SELECT 
                app_id, applicant_name, mobile, from_date, to_date,
                rooms_required, status, submitted_date, guest_details,
                room_status, check_in_date, check_out_date
            FROM applications ORDER BY submitted_date DESC
        ''')
        rows = cursor.fetchall()
    else:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                app_id, applicant_name, mobile, from_date, to_date,
                rooms_required, status, submitted_date, guest_details,
                room_status, check_in_date, check_out_date
            FROM applications ORDER BY submitted_date DESC
        ''')
        rows = cursor.fetchall()
    
    result = []
    for row in rows:
        if USE_POSTGRES:
            guest_details = row['guest_details']
        else:
            guest_details = row['guest_details']
        
        guest_count = 0
        adult_count = 0
        child_count = 0
        
        if guest_details:
            try:
                guests = json.loads(guest_details)
                guest_count = len(guests)
                adult_count = len([g for g in guests if g.get('guest_type') == 'Adult'])
                child_count = len([g for g in guests if g.get('guest_type') == 'Child'])
            except:
                pass
        
        if USE_POSTGRES:
            result.append({
                'app_id': row['app_id'],
                'applicant_name': row['applicant_name'] or 'N/A',
                'mobile': row['mobile'] or 'N/A',
                'from_date': row['from_date'] or 'N/A',
                'to_date': row['to_date'] or 'N/A',
                'rooms_required': row['rooms_required'] or 1,
                'status': row['status'] or 'Pending',
                'submitted_date': str(row['submitted_date']) if row['submitted_date'] else '',
                'guest_count': guest_count,
                'adult_count': adult_count,
                'child_count': child_count,
                'room_status': row['room_status'] or 'Booked',
                'check_in_date': row['check_in_date'],
                'check_out_date': row['check_out_date']
            })
        else:
            result.append({
                'app_id': row[0],
                'applicant_name': row[1] or 'N/A',
                'mobile': row[2] or 'N/A',
                'from_date': row[3] or 'N/A',
                'to_date': row[4] or 'N/A',
                'rooms_required': row[5] or 1,
                'status': row[6] or 'Pending',
                'submitted_date': row[7] or '',
                'guest_count': guest_count,
                'adult_count': adult_count,
                'child_count': child_count,
                'room_status': row[9] or 'Booked',
                'check_in_date': row[10],
                'check_out_date': row[11]
            })
    
    conn.close()
    return result

def get_application_by_id(app_id):
    """Get single application"""
    conn = get_db_connection()
    
    if USE_POSTGRES:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT * FROM applications WHERE app_id = %s', (app_id,))
        row = cursor.fetchone()
    else:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM applications WHERE app_id = ?', (app_id,))
        row = cursor.fetchone()
    
    conn.close()
    return dict(row) if row else None

def update_application_status(app_id, status, approved_by='Admin'):
    """Update application status"""
    conn = get_db_connection()
    
    if USE_POSTGRES:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE applications SET status=%s, approved_by=%s, approved_date=CURRENT_TIMESTAMP
            WHERE app_id=%s
        ''', (status, approved_by, app_id))
    else:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE applications SET status=?, approved_by=?, approved_date=CURRENT_TIMESTAMP
            WHERE app_id=?
        ''', (status, approved_by, app_id))
    
    conn.commit()
    conn.close()

def delete_application(app_id):
    """Delete application"""
    conn = get_db_connection()
    
    if USE_POSTGRES:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM applications WHERE app_id=%s', (app_id,))
    else:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM applications WHERE app_id=?', (app_id,))
    
    conn.commit()
    conn.close()

def verify_admin(username, password):
    """Verify admin credentials"""
    conn = get_db_connection()
    hashed = hashlib.sha256(password.encode()).hexdigest()
    
    if USE_POSTGRES:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT * FROM admin WHERE username=%s AND password=%s', (username, hashed))
        admin = cursor.fetchone()
    else:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM admin WHERE username=? AND password=?', (username, hashed))
        admin = cursor.fetchone()
    
    conn.close()
    return admin is not None

# ==================== CHECK-IN / CHECK-OUT FUNCTIONS ====================

def check_in_application(app_id, admin_name):
    conn = get_db_connection()
    
    if USE_POSTGRES:
        cursor = conn.cursor()
        cursor.execute('SELECT room_status FROM applications WHERE app_id=%s', (app_id,))
        current = cursor.fetchone()
        
        if current and current[0] == 'Occupied':
            conn.close()
            return False, "Already checked in!"
        
        cursor.execute('''
            UPDATE applications SET check_in_date=CURRENT_TIMESTAMP, room_status='Occupied'
            WHERE app_id=%s
        ''', (app_id,))
    else:
        cursor = conn.cursor()
        cursor.execute('SELECT room_status FROM applications WHERE app_id=?', (app_id,))
        current = cursor.fetchone()
        
        if current and current[0] == 'Occupied':
            conn.close()
            return False, "Already checked in!"
        
        cursor.execute('''
            UPDATE applications SET check_in_date=CURRENT_TIMESTAMP, room_status='Occupied'
            WHERE app_id=?
        ''', (app_id,))
    
    conn.commit()
    conn.close()
    return True, "Checked in successfully!"

def check_out_application(app_id):
    conn = get_db_connection()
    
    if USE_POSTGRES:
        cursor = conn.cursor()
        cursor.execute('SELECT room_status FROM applications WHERE app_id=%s', (app_id,))
        current = cursor.fetchone()
        
        if current and current[0] == 'Vacant':
            conn.close()
            return False, "Already checked out!"
        
        cursor.execute('''
            UPDATE applications SET check_out_date=CURRENT_TIMESTAMP, room_status='Vacant'
            WHERE app_id=%s
        ''', (app_id,))
    else:
        cursor = conn.cursor()
        cursor.execute('SELECT room_status FROM applications WHERE app_id=?', (app_id,))
        current = cursor.fetchone()
        
        if current and current[0] == 'Vacant':
            conn.close()
            return False, "Already checked out!"
        
        cursor.execute('''
            UPDATE applications SET check_out_date=CURRENT_TIMESTAMP, room_status='Vacant'
            WHERE app_id=?
        ''', (app_id,))
    
    conn.commit()
    conn.close()
    return True, "Checked out successfully!"

def get_current_occupancy():
    conn = get_db_connection()
    
    if USE_POSTGRES:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('''
            SELECT * FROM applications WHERE room_status='Occupied' AND check_out_date IS NULL
            ORDER BY check_in_date DESC
        ''')
        rows = cursor.fetchall()
    else:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM applications WHERE room_status='Occupied' AND check_out_date IS NULL
            ORDER BY check_in_date DESC
        ''')
        rows = cursor.fetchall()
    
    conn.close()
    return [dict(row) for row in rows]

def get_room_status_count():
    conn = get_db_connection()
    TOTAL_ROOMS = 250
    
    if USE_POSTGRES:
        cursor = conn.cursor()
        cursor.execute('SELECT COALESCE(SUM(rooms_required), 0) FROM applications WHERE room_status=%s', ('Occupied',))
        occupied = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT COALESCE(SUM(rooms_required), 0) FROM applications WHERE status=%s AND (room_status=%s OR room_status IS NULL)', ('Approved', 'Booked'))
        booked = cursor.fetchone()[0] or 0
    else:
        cursor = conn.cursor()
        cursor.execute('SELECT COALESCE(SUM(rooms_required), 0) FROM applications WHERE room_status="Occupied"')
        occupied = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT COALESCE(SUM(rooms_required), 0) FROM applications WHERE status="Approved" AND (room_status="Booked" OR room_status IS NULL)')
        booked = cursor.fetchone()[0] or 0
    
    vacant = TOTAL_ROOMS - occupied - booked
    conn.close()
    
    return {'occupied': occupied, 'booked': booked, 'vacant': vacant}