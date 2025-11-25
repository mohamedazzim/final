import sys, os
sys.path.append(os.getcwd())
from scraper import get_scraper_progress

progress = get_scraper_progress()
print(progress)
