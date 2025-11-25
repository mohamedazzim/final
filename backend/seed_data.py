import os
import sys
from datetime import date, time
from sqlalchemy.orm import Session

from database import SessionLocal, engine, Base
from models import User, UserRole, Cause
from routers.auth import get_password_hash

def seed_database():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        print("Checking for existing users...")
        existing_user = db.query(User).filter(User.username == "admin").first()
        if not existing_user:
            print("Creating admin user...")
            # Ensure password is properly encoded as bytes for bcrypt
            password = "admin"
            if isinstance(password, str):
                password = password.encode('utf-8')
            admin_user = User(
                username="admin",
                email="admin@mhc.gov.in",
                hashed_password=get_password_hash(password.decode('utf-8') if isinstance(password, bytes) else password),
                role=UserRole.SUPERADMIN
            )
            db.add(admin_user)
            print("✓ Admin user created (username: admin, password: admin)")
        else:
            print("✓ Admin user already exists")
        
        print("\nChecking for existing causes...")
        existing_causes = db.query(Cause).count()
        if existing_causes == 0:
            print("Adding sample cause data...")
            
            sample_causes = [
                Cause(
                    court_no="1",
                    case_no="W.P. No. 12345 of 2024",
                    petitioner="Arulmigu Sri Ranganathaswamy Temple",
                    respondent="Tamil Nadu HRCE Department",
                    advocate="Mr. A. Krishnan",
                    hearing_date=date(2024, 12, 15),
                    hearing_time=time(10, 30),
                    case_type="Writ Petition",
                    raw_text="W.P. No. 12345 of 2024 - Arulmigu Sri Ranganathaswamy Temple vs Tamil Nadu HRCE Department - Court No. 1 - Adv: Mr. A. Krishnan - Date: 15-12-2024",
                    is_hrce=True
                ),
                Cause(
                    court_no="2",
                    case_no="W.P. No. 12346 of 2024",
                    petitioner="M/s. ABC Private Limited",
                    respondent="State of Tamil Nadu",
                    advocate="Ms. B. Lakshmi",
                    hearing_date=date(2024, 12, 16),
                    hearing_time=time(11, 0),
                    case_type="Writ Petition",
                    raw_text="W.P. No. 12346 of 2024 - M/s. ABC Private Limited vs State of Tamil Nadu - Court No. 2 - Adv: Ms. B. Lakshmi - Date: 16-12-2024",
                    is_hrce=False
                ),
                Cause(
                    court_no="1",
                    case_no="W.P. No. 12347 of 2024",
                    petitioner="Devasthanam Board",
                    respondent="Commissioner of HRCE",
                    advocate="Mr. C. Venkatesh",
                    hearing_date=date(2024, 12, 17),
                    hearing_time=time(14, 0),
                    case_type="Writ Petition",
                    raw_text="W.P. No. 12347 of 2024 - Devasthanam Board vs Commissioner of HRCE - Court No. 1 - Adv: Mr. C. Venkatesh - Date: 17-12-2024",
                    is_hrce=True
                ),
                Cause(
                    court_no="3",
                    case_no="CRL.A. No. 567 of 2024",
                    petitioner="K. Murugan",
                    respondent="State of Tamil Nadu",
                    advocate="Mr. D. Ramesh",
                    hearing_date=date(2024, 12, 18),
                    hearing_time=time(10, 0),
                    case_type="Criminal Appeal",
                    raw_text="CRL.A. No. 567 of 2024 - K. Murugan vs State of Tamil Nadu - Court No. 3 - Adv: Mr. D. Ramesh - Date: 18-12-2024",
                    is_hrce=False
                ),
                Cause(
                    court_no="2",
                    case_no="W.P. No. 12348 of 2024",
                    petitioner="Sri Parthasarathy Temple Trust",
                    respondent="Tamil Nadu State Government",
                    advocate="Mr. A. Krishnan",
                    hearing_date=date(2024, 12, 19),
                    hearing_time=time(11, 30),
                    case_type="Writ Petition",
                    raw_text="W.P. No. 12348 of 2024 - Sri Parthasarathy Temple Trust vs Tamil Nadu State Government - Court No. 2 - Adv: Mr. A. Krishnan - Date: 19-12-2024",
                    is_hrce=True
                ),
                Cause(
                    court_no="1",
                    case_no="O.S.A. No. 234 of 2024",
                    petitioner="R. Kumar",
                    respondent="S. Selvam",
                    advocate="Ms. E. Priya",
                    hearing_date=date(2024, 12, 20),
                    hearing_time=time(15, 0),
                    case_type="Original Side Appeal",
                    raw_text="O.S.A. No. 234 of 2024 - R. Kumar vs S. Selvam - Court No. 1 - Adv: Ms. E. Priya - Date: 20-12-2024",
                    is_hrce=False
                ),
                Cause(
                    court_no="4",
                    case_no="W.P. No. 12349 of 2024",
                    petitioner="Mutt Administration",
                    respondent="HRCE Department",
                    advocate="Mr. F. Subramaniam",
                    hearing_date=date(2024, 12, 21),
                    hearing_time=time(10, 45),
                    case_type="Writ Petition",
                    raw_text="W.P. No. 12349 of 2024 - Mutt Administration vs HRCE Department - Court No. 4 - Adv: Mr. F. Subramaniam - Date: 21-12-2024",
                    is_hrce=True
                ),
                Cause(
                    court_no="3",
                    case_no="W.A. No. 789 of 2024",
                    petitioner="XYZ Corporation",
                    respondent="Income Tax Department",
                    advocate="Mr. G. Arun",
                    hearing_date=date(2024, 12, 22),
                    hearing_time=time(14, 30),
                    case_type="Writ Appeal",
                    raw_text="W.A. No. 789 of 2024 - XYZ Corporation vs Income Tax Department - Court No. 3 - Adv: Mr. G. Arun - Date: 22-12-2024",
                    is_hrce=False
                ),
                Cause(
                    court_no="2",
                    case_no="W.P. No. 12350 of 2024",
                    petitioner="Arulmigu Meenakshi Temple",
                    respondent="Commissioner, Hindu Religious Endowments",
                    advocate="Ms. H. Divya",
                    hearing_date=date(2024, 12, 23),
                    hearing_time=time(11, 15),
                    case_type="Writ Petition",
                    raw_text="W.P. No. 12350 of 2024 - Arulmigu Meenakshi Temple vs Commissioner, Hindu Religious Endowments - Court No. 2 - Adv: Ms. H. Divya - Date: 23-12-2024",
                    is_hrce=True
                ),
                Cause(
                    court_no="1",
                    case_no="C.M.A. No. 456 of 2024",
                    petitioner="P. Ravi",
                    respondent="Chennai Corporation",
                    advocate="Mr. I. Ganesh",
                    hearing_date=date(2024, 12, 24),
                    hearing_time=time(10, 15),
                    case_type="Civil Miscellaneous Appeal",
                    raw_text="C.M.A. No. 456 of 2024 - P. Ravi vs Chennai Corporation - Court No. 1 - Adv: Mr. I. Ganesh - Date: 24-12-2024",
                    is_hrce=False
                ),
            ]
            
            db.bulk_save_objects(sample_causes)
            print(f"✓ Added {len(sample_causes)} sample cause records")
        else:
            print(f"✓ Database already has {existing_causes} cause records")
        
        db.commit()
        print("\n✅ Database seeding completed successfully!")
        print("\n📋 You can now:")
        print("   - Login with username: admin, password: admin")
        print("   - Search for cases including HRCE temple cases")
        print("   - View related cases and test fuzzy matching")
        
    except Exception as e:
        print(f"\n❌ Error seeding database: {str(e)}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
