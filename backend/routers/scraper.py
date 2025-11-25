from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from database import get_db
from models import User, UserRole, ScraperLog, Cause
from schemas import ScraperLogResponse, ScraperTriggerResponse, FetchCourtDataRequest
from routers.auth import get_current_user
from scraper import run_scraper, stop_scraper, get_scraper_progress, discover_available_courts, fetch_full_cause_list_json, process_court_cases, add_log

router = APIRouter()


def check_admin_or_superadmin(current_user: User):
    if current_user.role not in [UserRole.COURT_ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized. Admin access required.")


@router.post("/trigger", response_model=ScraperTriggerResponse)
def trigger_scraper(
    target_date: date = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_admin_or_superadmin(current_user)
    
    print(f"Triggering scraper with target_date: {target_date}")
    
    try:
        records_count = run_scraper(db, target_date)
        return ScraperTriggerResponse(
            message="Scraper completed successfully",
            status="success",
            records_extracted=records_count
        )
    except Exception as e:
        return ScraperTriggerResponse(
            message=f"Scraper failed: {str(e)}",
            status="error",
            records_extracted=0
        )


@router.get("/logs", response_model=List[ScraperLogResponse])
async def get_scraper_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_admin_or_superadmin(current_user)
    
    logs = db.query(ScraperLog).order_by(ScraperLog.created_at.desc()).limit(limit).all()
    return logs


@router.get("/status")
async def get_scraper_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_admin_or_superadmin(current_user)
    
    latest_log = db.query(ScraperLog).order_by(ScraperLog.created_at.desc()).first()
    
    if not latest_log:
        return {
            "status": "never_run",
            "last_run": None,
            "last_status": None,
            "total_records": 0
        }
    
    total_causes = db.query(Cause).count()
    
    return {
        "status": str(latest_log.status.value) if hasattr(latest_log.status, 'value') else str(latest_log.status),
        "last_run": latest_log.created_at,
        "last_status": str(latest_log.status.value) if hasattr(latest_log.status, 'value') else str(latest_log.status),
        "total_records": total_causes,
        "last_extraction_count": latest_log.records_extracted
    }


@router.post("/stop")
async def stop_scraper_endpoint(
    current_user: User = Depends(get_current_user)
):
    check_admin_or_superadmin(current_user)
    stop_scraper()
    return {"message": "Scraper stop requested"}


@router.get("/progress")
async def get_progress(
    current_user: User = Depends(get_current_user)
):
    check_admin_or_superadmin(current_user)
    return get_scraper_progress()


@router.get("/discover-courts")
async def discover_courts(
    target_date: str,
    court_start: int = 1,
    court_end: int = 75,
    current_user: User = Depends(get_current_user)
):
    check_admin_or_superadmin(current_user)
    
    try:
        available_courts = discover_available_courts(target_date, (court_start, court_end))
        return {
            "date": target_date,
            "total_courts_checked": court_end - court_start + 1,
            "courts_with_data": len(available_courts),
            "courts": available_courts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error discovering courts: {str(e)}")


@router.post("/fetch-court-data")
async def fetch_and_save_court_data(
    request: FetchCourtDataRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_admin_or_superadmin(current_user)
    
    total_cases_saved = 0
    results = []
    
    add_log(f"🚀 Starting data fetch for {len(request.court_numbers)} courts...")
    add_log(f"📅 Target Date: {request.target_date}")
    add_log(f"🏛️ Requested Courts: {', '.join(request.court_numbers[:5])}{'...' if len(request.court_numbers) > 5 else ''}")
    
    try:
        hearing_date = date.fromisoformat(request.target_date)
        
        # Fetch full JSON once
        add_log(f"📥 Fetching full cause list data for {request.target_date}...")
        full_data_response = fetch_full_cause_list_json(request.target_date)
        
        if not full_data_response['success']:
            error_msg = full_data_response.get('error', 'Failed to fetch data')
            add_log(f"❌ Fetch failed: {error_msg}")
            raise Exception(error_msg)
            
        full_json_data = full_data_response['data']
        add_log(f"✅ Successfully fetched {len(full_json_data)} records from API")
        
        if len(full_json_data) == 0:
            add_log(f"⚠️ WARNING: API returned 0 records for date {request.target_date}")
            add_log(f"Data fetch complete. Total cases saved: 0")
            return {
                "total_cases_saved": 0,
                "courts_processed": 0,
                "results": []
            }
        
        add_log(f"🔍 Sample JSON court: '{full_json_data[0].get('courtno')}'")
        add_log(f"🔍 Processing {len(request.court_numbers)} courts...")
        
        for i, court_num in enumerate(request.court_numbers):
            court_num = court_num.strip()
            
            try:
                # Process data for this specific court
                cases = process_court_cases(full_json_data, court_num, hearing_date)
                
                if cases:
                    cause_objects = [Cause(**case_data) for case_data in cases]
                    db.bulk_save_objects(cause_objects)
                    db.commit()
                    total_cases_saved += len(cause_objects)
                    
                    if i < 3 or (i + 1) % 5 == 0:
                        add_log(f"✅ Court {court_num}: Saved {len(cause_objects)} cases")
                    
                    results.append({
                        "court_number": court_num,
                        "success": True,
                        "cases_saved": len(cause_objects)
                    })
                else:
                    if i < 3:
                        add_log(f"⚠️ Court {court_num}: No cases found")
                    
                    results.append({
                        "court_number": court_num,
                        "success": True,
                        "cases_saved": 0,
                        "message": "No cases found"
                    })
                    
            except Exception as e:
                add_log(f"❌ Court {court_num} ERROR: {str(e)}")
                import traceback
                add_log(f"📍 Traceback: {traceback.format_exc()[:200]}")
                results.append({
                    "court_number": court_num,
                    "success": False,
                    "error": str(e)
                })
        
        add_log(f"Data fetch complete. Total cases saved: {total_cases_saved}")
        return {
            "total_cases_saved": total_cases_saved,
            "courts_processed": len(request.court_numbers),
            "results": results
        }
        
    except Exception as e:
        add_log(f"Critical error during data fetch: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching court data: {str(e)}")
