import sys, os, asyncio
sys.path.append(os.getcwd())

from routers import scraper as scraper_router
from schemas import FetchCourtDataRequest
from routers.scraper import discover_available_courts
from database import SessionLocal
from models import User, UserRole

async def main():
    target_date = "2025-11-24"
    courts = discover_available_courts(target_date)
    court_nums = [c['court_number'] for c in courts]
    print(f"courts: {len(court_nums)}")
    request = FetchCourtDataRequest(target_date=target_date, court_numbers=court_nums)
    db = SessionLocal()
    try:
        current_user = User(role=UserRole.SUPERADMIN)
        result = await scraper_router.fetch_and_save_court_data(request, db, current_user)
        print(result)
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
