from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

from database import engine, Base, SessionLocal
from routers import cases, scraper, auth, admin
from scraper import run_scraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def scheduled_scraper_job():
    """Run the scraper as a scheduled job"""
    db = SessionLocal()
    try:
        logger.info("Running scheduled scraper job...")
        records_count = run_scraper(db)
        logger.info(f"Scheduled scraper completed: {records_count} records extracted")
    except Exception as e:
        logger.error(f"Scheduled scraper failed: {str(e)}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    
    scheduler.add_job(
        scheduled_scraper_job,
        CronTrigger(hour=2, minute=0),
        id='daily_scraper',
        name='Daily Cause List Scraper',
        replace_existing=True
    )
    scheduler.start()
    logger.info("APScheduler started - Daily scraper will run at 2:00 AM")
    
    yield
    
    scheduler.shutdown()
    logger.info("APScheduler shut down")


app = FastAPI(
    title="Madras High Court Cause List API",
    description="API for automated extraction and search of Madras High Court cause lists",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(cases.router, prefix="/api/cases", tags=["Cases"])
app.include_router(scraper.router, prefix="/api/scraper", tags=["Scraper"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])


@app.get("/")
async def root():
    return {
        "message": "Madras High Court Cause List API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
