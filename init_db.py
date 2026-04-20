# init_db.py
from database import init_database

if __name__ == "__main__":
    print("🚀 Initializing HMC Hostel Database...")
    init_database()
    print("✅ Database setup complete!")
    print("\n📝 Login Credentials:")
    print("   Username: admin")
    print("   Password: admin123")