from database import engine, Base, SessionLocal
from models import User, UserRole
from routers.auth import get_password_hash

def reset_database():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        print("Creating admin user...")
        admin_user = User(
            username="admin",
            email="admin@mhc.gov.in",
            hashed_password=get_password_hash("admin"),
            role=UserRole.SUPERADMIN
        )
        db.add(admin_user)
        db.commit()
        print("✓ Admin user created (username: admin, password: admin)")
        print("✓ Database reset successfully!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_database()
