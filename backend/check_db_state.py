from database import SessionLocal
from models import User, Cause

db = SessionLocal()
try:
    user_count = db.query(User).count()
    cause_count = db.query(Cause).count()
    print(f"Users: {user_count}")
    print(f"Causes: {cause_count}")
finally:
    db.close()
