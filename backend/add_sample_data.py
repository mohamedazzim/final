from database import SessionLocal, Base, engine
from models import Cause
from datetime import date, time, timedelta

Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    existing_count = db.query(Cause).count()
    if existing_count > 0:
        print(f"Database already has {existing_count} causes. Skipping sample data creation.")
    else:
        sample_causes = [
            Cause(
                sr_no="1",
                court_no="COURT NO. 1",
                case_no="WP/12345/2024",
                petitioner="Arulmigu Kapaleeswarar Temple",
                respondent="Commissioner, HRCE Department",
                advocate="Mr. R. Krishnamurthy",
                hearing_date=date.today() + timedelta(days=1),
                hearing_time=time(10, 30),
                case_type="Writ Petition",
                raw_text="1 WP/12345/2024 Arulmigu Kapaleeswarar Temple",
                is_hrce=True
            ),
            Cause(
                sr_no="2",
                court_no="COURT NO. 1",
                case_no="WA/23456/2024",
                petitioner="M/s. Chennai Corporation",
                respondent="State of Tamil Nadu",
                advocate="Mrs. S. Lakshmi",
                hearing_date=date.today() + timedelta(days=1),
                hearing_time=time(10, 45),
                case_type="Writ Appeal",
                raw_text="2 WA/23456/2024 M/s. Chennai Corporation",
                is_hrce=False
            ),
            Cause(
                sr_no="3",
                court_no="COURT NO. 2",
                case_no="CRL.P/34567/2024",
                petitioner="Devasthanam Board",
                respondent="State of Tamil Nadu",
                advocate="Dr. K. Venkatesh",
                hearing_date=date.today() + timedelta(days=1),
                hearing_time=time(11, 0),
                case_type="Criminal Petition",
                raw_text="3 CRL.P/34567/2024 Devasthanam Board",
                is_hrce=True
            ),
            Cause(
                sr_no="4",
                court_no="COURT NO. 2",
                case_no="OS/45678/2024",
                petitioner="Tamil Nadu Housing Board",
                respondent="ABC Private Ltd",
                advocate="Mr. P. Ramesh",
                hearing_date=date.today() + timedelta(days=1),
                hearing_time=time(11, 15),
                case_type="Original Side",
                raw_text="4 OS/45678/2024 Tamil Nadu Housing Board",
                is_hrce=False
            ),
            Cause(
                sr_no="5",
                court_no="COURT NO. 3",
                case_no="WP/56789/2024",
                petitioner="Hindu Religious Trust",
                respondent="Commissioner of HRCE",
                advocate="Ms. M. Priya",
                hearing_date=date.today() + timedelta(days=1),
                hearing_time=time(11, 30),
                case_type="Writ Petition",
                raw_text="5 WP/56789/2024 Hindu Religious Trust",
                is_hrce=True
            ),
            Cause(
                sr_no="6",
                court_no="COURT NO. 3",
                case_no="CMA/67890/2024",
                petitioner="Greater Chennai Corporation",
                respondent="XYZ Developers",
                advocate="Mr. S. Kumar",
                hearing_date=date.today() + timedelta(days=1),
                hearing_time=time(11, 45),
                case_type="Civil Miscellaneous Appeal",
                raw_text="6 CMA/67890/2024 Greater Chennai Corporation",
                is_hrce=False
            ),
            Cause(
                sr_no="7",
                court_no="COURT NO. 4",
                case_no="WP/78901/2024",
                petitioner="Arulmigu Murugan Temple Board",
                respondent="State of Tamil Nadu",
                advocate="Dr. V. Raman",
                hearing_date=date.today() + timedelta(days=2),
                hearing_time=time(10, 0),
                case_type="Writ Petition",
                raw_text="7 WP/78901/2024 Arulmigu Murugan Temple Board",
                is_hrce=True
            ),
            Cause(
                sr_no="8",
                court_no="COURT NO. 4",
                case_no="SA/89012/2024",
                petitioner="Tamil Nadu State Transport",
                respondent="Union of India",
                advocate="Mrs. A. Devi",
                hearing_date=date.today() + timedelta(days=2),
                hearing_time=time(10, 15),
                case_type="Second Appeal",
                raw_text="8 SA/89012/2024 Tamil Nadu State Transport",
                is_hrce=False
            ),
            Cause(
                sr_no="9",
                court_no="COURT NO. 5",
                case_no="WP/90123/2024",
                petitioner="Charitable Endowments Board",
                respondent="HRCE Commissioner",
                advocate="Mr. N. Subramanian",
                hearing_date=date.today() + timedelta(days=2),
                hearing_time=time(10, 30),
                case_type="Writ Petition",
                raw_text="9 WP/90123/2024 Charitable Endowments Board",
                is_hrce=True
            ),
            Cause(
                sr_no="10",
                court_no="COURT NO. 5",
                case_no="CRP/01234/2024",
                petitioner="Public Works Department",
                respondent="ABC Construction Co.",
                advocate="Ms. R. Vasanthi",
                hearing_date=date.today() + timedelta(days=2),
                hearing_time=time(10, 45),
                case_type="Civil Revision Petition",
                raw_text="10 CRP/01234/2024 Public Works Department",
                is_hrce=False
            ),
        ]
        
        db.bulk_save_objects(sample_causes)
        db.commit()
        print(f"Successfully added {len(sample_causes)} sample causes to the database.")
        print("Sample data includes:")
        print(f"  - {sum(1 for c in sample_causes if c.is_hrce)} HRCE-related cases")
        print(f"  - Cases across {len(set(c.court_no for c in sample_causes))} different courts")
        print(f"  - Hearing dates: {date.today() + timedelta(days=1)} and {date.today() + timedelta(days=2)}")
        
except Exception as e:
    print(f"Error adding sample data: {e}")
    db.rollback()
finally:
    db.close()
