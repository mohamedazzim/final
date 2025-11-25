import requests
import urllib3
from bs4 import BeautifulSoup
from datetime import datetime, date
from sqlalchemy.orm import Session
import re
import pdfplumber
import os
import tempfile
import time
import base64
from typing import List, Dict

from models import Cause, ScraperLog, ScraperStatus

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://www.mhc.tn.gov.in/judis/clists/clists-madras"
DATE_API_URL = f"{BASE_URL}/api/getDate.php?toc=1"
PDF_BASE_URL = f"{BASE_URL}/causelists/pdf"

HRCE_KEYWORDS = [
    "HRCE",
    "Hindu Religious",
    "Charitable Endowments",
    "Temple",
    "Devasthanam",
    "Devaswom",
    "Mutt",
    "Religious Trust",
    "Dharmada",
    "Arulmigu"
]

SPECIAL_COURTS = [
    "VIDEO CONFERENCING"
]


# Utility helpers
def sanitize_text(value) -> str:
    """Ensure DB text fields always receive plain strings."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (list, tuple, set)):
        parts = []
        for v in value:
            cleaned = sanitize_text(v)
            if cleaned:
                parts.append(cleaned)
        return ", ".join(parts).strip()
    return str(value).strip()


# Global state for scraper control
SCRAPER_STATE = {
    "is_running": False,
    "stop_requested": False,
    "current_action": "Idle",
    "logs": []
}

def add_log(message: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    SCRAPER_STATE["logs"].insert(0, log_entry)
    # Keep only last 50 logs
    if len(SCRAPER_STATE["logs"]) > 50:
        SCRAPER_STATE["logs"].pop()
    SCRAPER_STATE["current_action"] = message

def stop_scraper():
    if SCRAPER_STATE["is_running"]:
        SCRAPER_STATE["stop_requested"] = True
        add_log("Stop requested by user...")
        return True
    return False

def get_scraper_progress():
    return SCRAPER_STATE

def detect_hrce_case(text: str) -> bool:
    if not text:
        return False
    text_upper = text.upper()
    return any(keyword.upper() in text_upper for keyword in HRCE_KEYWORDS)

def fetch_available_dates():
    max_retries = 2
    for attempt in range(max_retries):
        try:
            add_log(f"Fetching dates (attempt {attempt + 1}/{max_retries})...")
            response = requests.get(DATE_API_URL, verify=False, timeout=30)
            response.raise_for_status()
            data = response.json()
            # data is list of dicts: [{"doc":"2025-11-24"}, ...]
            dates = [item['doc'] for item in data]
            add_log(f"Successfully fetched {len(dates)} dates")
            return dates
        except requests.exceptions.Timeout:
            add_log(f"Timeout on attempt {attempt + 1}. Giving up.")
            return []
        except Exception as e:
            add_log(f"Error fetching dates: {str(e)[:100]}")
            return []
    
    return []

def download_pdf(date_str):
    # date_str is YYYY-MM-DD
    # PDF filename format: cause_DDMMYYYY.pdf
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    filename = f"cause_{dt.strftime('%d%m%Y')}.pdf"
    url = f"{PDF_BASE_URL}/{filename}"
    
    max_retries = 2
    
    for attempt in range(max_retries):
        try:
            add_log(f"Downloading {filename} (attempt {attempt + 1}/{max_retries})...")
            
            response = requests.get(url, verify=False, timeout=30, stream=True)
            if response.status_code == 200:
                fd, path = tempfile.mkstemp(suffix=".pdf")
                with os.fdopen(fd, 'wb') as tmp:
                    for chunk in response.iter_content(chunk_size=8192):
                        tmp.write(chunk)
                
                file_size = os.path.getsize(path)
                add_log(f"Downloaded successfully ({file_size} bytes)")
                return path
            else:
                add_log(f"HTTP error: {response.status_code}. Giving up.")
                return None
        except requests.exceptions.Timeout:
            add_log(f"Download timeout on attempt {attempt + 1}. Giving up.")
            return None
        except requests.exceptions.ConnectionError as e:
            add_log(f"Connection error: {str(e)[:80]}")
            return None
        except Exception as e:
            add_log(f"Error downloading PDF: {str(e)[:100]}")
            return None
    
    add_log(f"Failed to download {filename}")
    return None

def parse_pdf_content(pdf_path, hearing_date):
    causes = []
    current_court = None
    
    # Regex patterns
    court_pattern = re.compile(r"COURT\s+NO\.\s+(\d+\s*[a-zA-Z]?)")
    # Main case pattern: SrNo CaseNo Rest
    main_case_pattern = re.compile(r"^(\d+)\s+([A-Z]+(?:[/ ][A-Za-z0-9]+)?[/ ]\d+/\d+)\s+(.*)")
    # Connected case pattern: (AND)? CaseNo Rest
    # Matches lines starting with AND or just whitespace, then a case number
    connected_case_pattern = re.compile(r"^\s*(?:AND)?\s*([A-Z]+(?:[/ ][A-Za-z0-9]+)?[/ ]\d+/\d+)\s+(.*)")
    # Pattern for just "AND" on a line, implying next line has case info
    and_only_pattern = re.compile(r"^\s*AND\s*$")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                    
                lines = text.split('\n')
                
                # Try to find court number
                for line in lines:
                    match = court_pattern.search(line)
                    if match:
                        current_court = f"COURT NO. {match.group(1)}"
                
                i = 0
                current_sr_no = None
                
                while i < len(lines):
                    line = lines[i].strip()
                    if not line:
                        i += 1
                        continue

                    # Check for Main Case
                    main_match = main_case_pattern.match(line)
                    connected_match = connected_case_pattern.match(line)
                    and_only_match = and_only_pattern.match(line)
                    
                    is_main = bool(main_match)
                    is_connected = bool(connected_match) and not is_main
                    is_and_only = bool(and_only_match)
                    
                    if is_main and main_match:
                        current_sr_no = main_match.group(1)
                        case_no = main_match.group(2)
                        rest_of_line = main_match.group(3)
                    elif is_connected and current_sr_no and connected_match:
                        # It's a connected case under the current Sr No
                        case_no = connected_match.group(1)
                        rest_of_line = connected_match.group(2)
                    elif is_and_only and current_sr_no:
                        # "AND" is on this line, check next line for case no
                        if i + 1 < len(lines):
                            next_line = lines[i+1].strip()
                            # Try to match case pattern on next line
                            # It might not have "AND" prefix since "AND" was on previous line
                            # But we can reuse connected_case_pattern or just look for case no
                            next_match = re.match(r"^\s*([A-Z]+(?:[/ ][A-Za-z0-9]+)?[/ ]\d+/\d+)\s+(.*)", next_line)
                            if next_match:
                                case_no = next_match.group(1)
                                rest_of_line = next_match.group(2)
                                i += 1 # Skip the next line since we consumed it
                            else:
                                i += 1
                                continue
                        else:
                            i += 1
                            continue
                    else:
                        # Not a case line, move on
                        i += 1
                        continue
                        
                    # Common parsing logic for both main and connected cases
                    # Improved Petitioner/Advocate separation
                    # Look for common advocate prefixes
                    adv_split = re.split(r'\s+(M/S\.|Mr\.|Ms\.|Mrs\.|Dr\.|Adv\.)', rest_of_line, 1)
                    
                    if len(adv_split) >= 3:
                        petitioner = adv_split[0].strip()
                        advocate = (adv_split[1] + adv_split[2]).strip()
                    else:
                        # Fallback to double space split
                        parts = re.split(r'\s{2,}', rest_of_line)
                        petitioner = parts[0] if len(parts) > 0 else ""
                        advocate = parts[1] if len(parts) > 1 else ""
                    
                    case_type = ""
                    respondent = ""
                    
                    # Look ahead for next lines to find VS and Respondent
                    # The structure is usually:
                    # Line 1: Seq CaseNo Petitioner Advocate
                    # Line 2: (CaseType) VS
                    # Line 3: Respondent Location
                    
                    # Check next few lines
                    j = 1
                    found_vs = False
                    
                    # We need to be careful not to consume the next case's line
                    while i + j < len(lines) and j <= 5: # Increased lookahead slightly
                        next_line = lines[i+j].strip()
                        
                        # Stop if next line looks like a new case
                        if main_case_pattern.match(next_line) or connected_case_pattern.match(next_line) or and_only_pattern.match(next_line):
                            break
                        
                        # Check for Case Type
                        if not case_type and "(" in next_line:
                                case_type_match = re.search(r"\((.*?)\)", next_line)
                                if case_type_match:
                                    case_type = case_type_match.group(1)
                        
                        # Check for VS
                        if "VS" in next_line or "vs" in next_line.lower():
                            found_vs = True
                            # Sometimes VS is on the same line as Respondent
                            # or Respondent is on the next line
                            
                            # If there is text after VS, it might be respondent
                            vs_parts = re.split(r'VS|vs', next_line, flags=re.IGNORECASE)
                            if len(vs_parts) > 1 and len(vs_parts[1].strip()) > 3:
                                    # Likely respondent is here
                                    respondent = vs_parts[1].strip()
                                    # Clean up dashes
                                    respondent = re.sub(r'^-+\s*', '', respondent)
                            
                        elif found_vs and not respondent:
                            # This line is likely the respondent
                            respondent = next_line.split('   ')[0].strip()
                            # Don't break immediately, might find more info or clean up
                            break
                        
                        j += 1
                        
                    cause_data = {
                        "sr_no": current_sr_no,
                        "court_no": current_court,
                        "case_no": case_no,
                        "petitioner": petitioner,
                        "respondent": respondent,
                        "advocate": advocate,
                        "hearing_date": hearing_date,
                        "case_type": case_type,
                        "raw_text": line,
                        "is_hrce": detect_hrce_case(petitioner) or detect_hrce_case(respondent) or detect_hrce_case(line)
                    }
                    causes.append(cause_data)
                    i += 1
                    
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        
    return causes

def scrape_cause_list(db: Session, target_date: date | None = None) -> int:
    SCRAPER_STATE["is_running"] = True
    SCRAPER_STATE["stop_requested"] = False
    SCRAPER_STATE["logs"] = []
    total_extracted = 0
    
    add_log(f"Starting scraper run (JSON Mode). Target date: {target_date if target_date else 'All available'}")
    
    try:
        if target_date:
            dates = [target_date.strftime("%Y-%m-%d")]
        else:
            add_log("Fetching available dates from server...")
            dates = fetch_available_dates()
            
        add_log(f"Found {len(dates)} dates to process: {dates}")
        
        for date_str in dates:
            if SCRAPER_STATE["stop_requested"]:
                add_log("Scraper stopped by user request.")
                break
                
            add_log(f"Processing date: {date_str}")
            hearing_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            # Fetch JSON
            response = fetch_full_cause_list_json(date_str)
            
            if not response['success']:
                add_log(f"Failed to fetch JSON for {date_str}: {response.get('error')}")
                continue
                
            full_json_data = response['data']
            add_log(f"Fetched {len(full_json_data)} records. Processing...")
            
            # Delete existing records for this date
            db.query(Cause).filter(Cause.hearing_date == hearing_date).delete()
            db.commit()
            
            cases_to_save = []
            
            for item in full_json_data:
                try:
                    item_court = sanitize_text(item.get('courtno'))
                    if not item_court:
                        continue
                        
                    # Extract Main Case
                    case_type = sanitize_text(item.get('mcasetype'))
                    case_no_val = sanitize_text(item.get('mcaseno'))
                    case_yr = sanitize_text(item.get('mcaseyr'))
                    case_parts = [part for part in [case_type, case_no_val, case_yr] if part]
                    full_case_no = "/".join(case_parts)
                    
                    petitioner = sanitize_text(item.get('pname'))
                    respondent = sanitize_text(item.get('rname'))
                    advocate = sanitize_text(item.get('mpadv'))
                    
                    raw_text = sanitize_text(f"{item.get('serial_no')} {full_case_no} {petitioner} vs {respondent}")
                    
                    case_data = {
                        "sr_no": item.get('serial_no', ''),
                        "court_no": item_court,
                        "case_no": full_case_no,
                        "petitioner": petitioner,
                        "respondent": respondent,
                        "advocate": advocate,
                        "hearing_date": hearing_date,
                        "case_type": case_type,
                        "raw_text": raw_text,
                        "is_hrce": detect_hrce_case(petitioner) or detect_hrce_case(respondent) or detect_hrce_case(raw_text)
                    }
                    cases_to_save.append(case_data)
                    
                    # Extras
                    extras = item.get('extra', [])
                    if extras and isinstance(extras, list):
                        for extra in extras:
                            ex_case_type = sanitize_text(extra.get('excasetype'))
                            ex_case_no = sanitize_text(extra.get('excaseno'))
                            ex_case_yr = sanitize_text(extra.get('excaseyr'))
                            ex_parts = [part for part in [ex_case_type, ex_case_no, ex_case_yr] if part]
                            ex_full_case_no = "/".join(ex_parts)
                            ex_petitioner = sanitize_text(extra.get('expname'))
                            ex_respondent = sanitize_text(extra.get('exrname'))
                            ex_advocate = sanitize_text(extra.get('expadv'))
                            ex_raw_text = sanitize_text(f"Connected: {ex_full_case_no} {ex_petitioner} vs {ex_respondent}")
                            
                            ex_case_data = {
                                "sr_no": item.get('serial_no', ''),
                                "court_no": item_court,
                                "case_no": ex_full_case_no,
                                "petitioner": ex_petitioner,
                                "respondent": ex_respondent,
                                "advocate": ex_advocate,
                                "hearing_date": hearing_date,
                                "case_type": ex_case_type,
                                "raw_text": ex_raw_text,
                                "is_hrce": detect_hrce_case(ex_petitioner) or detect_hrce_case(ex_respondent) or detect_hrce_case(ex_raw_text)
                            }
                            cases_to_save.append(ex_case_data)
                            
                except Exception as e:
                    continue
            
            if cases_to_save:
                # Batch save
                batch_size = 1000
                for i in range(0, len(cases_to_save), batch_size):
                    batch = cases_to_save[i:i+batch_size]
                    cause_objects = [Cause(**data) for data in batch]
                    db.bulk_save_objects(cause_objects)
                    db.commit()
                
                total_extracted += len(cases_to_save)
                add_log(f"Successfully extracted {len(cases_to_save)} causes for {date_str}")
            else:
                add_log(f"No causes found in JSON for {date_str}")

        status = ScraperStatus.SUCCESS if not SCRAPER_STATE["stop_requested"] else ScraperStatus.ERROR
        log = ScraperLog(
            status=status,
            records_extracted=total_extracted,
            run_date=date.today(),
            error_message="Stopped by user" if SCRAPER_STATE["stop_requested"] else None
        )
        db.add(log)
        db.commit()
        
        add_log(f"Scraper finished. Total records: {total_extracted}")
        return total_extracted
    
    except Exception as e:
        add_log(f"Critical scraper error: {str(e)}")
        log = ScraperLog(
            status=ScraperStatus.ERROR,
            records_extracted=total_extracted,
            error_message=str(e),
            run_date=date.today()
        )
        db.add(log)
        db.commit()
        raise
    finally:
        SCRAPER_STATE["is_running"] = False
        SCRAPER_STATE["stop_requested"] = False


def run_scraper(db: Session, target_date: date | None = None) -> int:
    return scrape_cause_list(db, target_date)


def encode_date_base64(date_str: str) -> str:
    """Convert date string (YYYY-MM-DD) to base64"""
    return base64.b64encode(date_str.encode()).decode()


def encode_xml_filename_base64(date_str: str) -> str:
    """Convert date to XML filename format and encode to base64"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    filename = f"cause_{dt.strftime('%d%m%Y')}.xml"
    return base64.b64encode(filename.encode()).decode()


def discover_available_courts(target_date: str, court_range: tuple = (1, 60)) -> List[Dict]:
    """
    Discover which courts have active cause lists for a given date using the JSON API.
    
    Args:
        target_date: Date in YYYY-MM-DD format
        court_range: Tuple of (start, end) court numbers to check (ignored now as we fetch all)
    
    Returns:
        List of dicts with court information for courts that have data
    """
    available_courts = []
    
    SCRAPER_STATE["is_running"] = True
    add_log(f"Starting court discovery for {target_date}...")
    
    try:
        # Fetch the full JSON data once
        add_log("Fetching full cause list data from API...")
        response = fetch_full_cause_list_json(target_date)
        
        if not response['success']:
            add_log(f"❌ Failed to fetch data: {response.get('error')}")
            return []
            
        data = response['data']
        add_log(f"Successfully fetched {len(data)} records. Analyzing courts...")
        
        # Extract unique courts
        found_courts = {}
        
        for item in data:
            raw_court_name = item.get('courtno', '').strip()
            if not raw_court_name:
                continue
                
            # Normalize and group courts
            # Example: "COURT NO. 01 a" -> "01"
            # Example: "VIDEO CONFERENCING" -> "VIDEO CONFERENCING"
            
            court_id = None
            court_display_name = None
            
            # Check for numeric court pattern
            numeric_match = re.search(r'COURT\s+NO\.?\s*(\d+)', raw_court_name, re.IGNORECASE)
            
            if numeric_match:
                court_num = int(numeric_match.group(1))
                court_id = f"{court_num:02d}"
                court_display_name = f"COURT NO. {court_id}"
            elif any(special in raw_court_name.upper() for special in SPECIAL_COURTS):
                # Handle special courts
                for special in SPECIAL_COURTS:
                    if special in raw_court_name.upper():
                        court_id = special
                        court_display_name = special
                        break
            
            if court_id and court_display_name:
                if court_id not in found_courts:
                    # Try to extract judge name from the first occurrence
                    judge_name = "Unknown"
                    judge1 = item.get('judge1', '')
                    if judge1:
                        judge_name = judge1.replace('The Honourable', '').replace('Mr.Justice', '').strip()
                        
                    found_courts[court_id] = {
                        'court_number': court_id,
                        'court_name': court_display_name,
                        'judge': judge_name,
                        'url': '', # No specific URL needed anymore
                        'has_data': True
                    }
        
        # Convert to list and sort
        available_courts = list(found_courts.values())
        # Sort by court number (numeric) if possible, then special courts
        def sort_key(x):
            try:
                return int(x['court_number'])
            except ValueError:
                return 9999 # Put special courts at the end
                
        available_courts.sort(key=sort_key)
        
        add_log(f"Discovery complete. Found {len(available_courts)} active courts.")
        return available_courts
        
    except Exception as e:
        add_log(f"Critical error during discovery: {str(e)}")
        raise e
    finally:
        SCRAPER_STATE["is_running"] = False
        SCRAPER_STATE["stop_requested"] = False


def fetch_full_cause_list_json(target_date: str) -> Dict:
    """
    Fetch the full cause list JSON for a specific date.
    
    Args:
        target_date: Date in YYYY-MM-DD format
    
    Returns:
        Dict with success status and data
    """
    try:
        dt = datetime.strptime(target_date, "%Y-%m-%d")
        xml_filename = f"cause_{dt.strftime('%d%m%Y')}.xml"
        api_url = f"https://mhc.tn.gov.in/judis/clists/clists-madras/api/result.php?file={xml_filename}"
        
        add_log(f"Fetching full cause list from API: {api_url}")
        
        response = requests.get(api_url, verify=False, timeout=30)
        
        if response.status_code == 200:
            try:
                data = response.json()
                return {
                    'success': True,
                    'data': data,
                    'date': target_date
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': f"Failed to parse JSON: {str(e)}"
                }
        else:
            return {
                'success': False,
                'error': f"HTTP {response.status_code}"
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def normalize_court_name(court_str: str) -> str:
    """Normalize court name for comparison"""
    # Remove extra spaces, convert to upper
    return " ".join(court_str.upper().split())

def process_court_cases(json_data: List[Dict], court_number: str, hearing_date: date) -> List[Dict]:
    """
    Process JSON data to extract cases for a specific court.
    
    Args:
        json_data: List of case dictionaries from API
        court_number: Court number (e.g. "01" or "VIDEO CONFERENCING")
        hearing_date: Hearing date
    
    Returns:
        List of case dictionaries ready for DB
    """
    cases = []
    
    # Determine target court ID/Name for matching
    target_court_id = None
    target_special_name = None
    
    # Try to extract numeric ID from the requested court number
    # This handles "01", "1", "Court 1", "Court No. 1"
    try:
        # If it's a special court, don't try to extract number unless we are sure
        if not any(s in court_number.upper() for s in SPECIAL_COURTS):
            input_match = re.search(r'(\d+)', court_number)
            if input_match:
                target_court_id = int(input_match.group(1))
    except:
        pass
        
    # Also keep the string for special court matching or fallback
    target_special_name = court_number.upper()
    
    # Debug log (optional, can be removed if too noisy)
    # print(f"DEBUG: Processing court '{court_number}'. Target ID: {target_court_id}, Special: {target_special_name}")
    
    for item in json_data:
        # Check if this item belongs to the requested court
        # Handle potential None/null values safely
        raw_court = item.get('courtno')
        item_court = str(raw_court).strip() if raw_court else ''
        
        if not item_court:
            continue
            
        is_match = False
        
        # Try to extract numeric ID from the item court string
        item_court_id = None
        # Use a regex that looks for a number, but prefer "Court No X" format if possible
        # But for robustness, just finding the first distinct number is usually enough for these strings
        item_numeric_match = re.search(r'(\d+)', item_court)
        if item_numeric_match:
            item_court_id = int(item_numeric_match.group(1))
            
        # Logic:
        # 1. If both have IDs, compare IDs.
        # 2. If IDs match, it's a match.
        # 3. If IDs differ, it's NOT a match (prevents "1" matching "11").
        # 4. If one or both lack IDs, fall back to string matching.
        
        if target_court_id is not None and item_court_id is not None:
            if target_court_id == item_court_id:
                is_match = True
        elif target_court_id is None:
            # Only try string matching if we didn't have a specific numeric target
            # This prevents "Court 1" (ID 1) from matching "Court 11" (ID 11) via string containment if we were careless
            if target_special_name in item_court.upper():
                is_match = True
             
        if not is_match:
            continue
            
        # Extract Main Case
        try:
            # Construct case number
            case_type = sanitize_text(item.get('mcasetype'))
            case_no_val = sanitize_text(item.get('mcaseno'))
            case_yr = sanitize_text(item.get('mcaseyr'))
            
            case_parts = [part for part in [case_type, case_no_val, case_yr] if part]
            full_case_no = "/".join(case_parts)
            
            petitioner = sanitize_text(item.get('pname'))
            respondent = sanitize_text(item.get('rname'))
            advocate = sanitize_text(item.get('mpadv')) # Petitioner advocate
            
            # Create raw text representation
            raw_text = sanitize_text(f"{item.get('serial_no')} {full_case_no} {petitioner} vs {respondent}")
            
            case_data = {
                "sr_no": item.get('serial_no', ''),
                "court_no": item_court, # Use the actual court string from JSON
                "case_no": full_case_no,
                "petitioner": petitioner,
                "respondent": respondent,
                "advocate": advocate,
                "hearing_date": hearing_date,
                "case_type": case_type,
                "raw_text": raw_text,
                "is_hrce": detect_hrce_case(petitioner) or detect_hrce_case(respondent) or detect_hrce_case(raw_text)
            }
            cases.append(case_data)
            
            # Process Extra (Connected) Cases
            extras = item.get('extra', [])
            if extras and isinstance(extras, list):
                for extra in extras:
                    ex_case_type = sanitize_text(extra.get('excasetype'))
                    ex_case_no = sanitize_text(extra.get('excaseno'))
                    ex_case_yr = sanitize_text(extra.get('excaseyr'))
                    
                    ex_parts = [part for part in [ex_case_type, ex_case_no, ex_case_yr] if part]
                    ex_full_case_no = "/".join(ex_parts)
                    ex_petitioner = sanitize_text(extra.get('expname'))
                    ex_respondent = sanitize_text(extra.get('exrname'))
                    ex_advocate = sanitize_text(extra.get('expadv'))
                    
                    ex_raw_text = sanitize_text(f"Connected: {ex_full_case_no} {ex_petitioner} vs {ex_respondent}")
                    
                    ex_case_data = {
                        "sr_no": item.get('serial_no', ''), # Same serial no
                        "court_no": item_court,
                        "case_no": ex_full_case_no,
                        "petitioner": ex_petitioner,
                        "respondent": ex_respondent,
                        "advocate": ex_advocate,
                        "hearing_date": hearing_date,
                        "case_type": ex_case_type,
                        "raw_text": ex_raw_text,
                        "is_hrce": detect_hrce_case(ex_petitioner) or detect_hrce_case(ex_respondent) or detect_hrce_case(ex_raw_text)
                    }
                    cases.append(ex_case_data)
                    
        except Exception as e:
            add_log(f"Error processing case item: {str(e)}")
            continue
            
    return cases

def fetch_court_data_html(target_date: str, court_number: str) -> Dict:
    """
    Legacy function name kept for compatibility, but now uses JSON API.
    This is inefficient if called in a loop, but we'll optimize the router instead.
    """
    # This function is now deprecated in favor of fetch_full_cause_list_json
    # But we keep it for now if needed
    return {
        'success': False,
        'error': "Deprecated. Use fetch_full_cause_list_json instead."
    }

def parse_html_cause_list(html_content: str, court_number: str, hearing_date: date) -> List[Dict]:
    """
    Deprecated.
    """
    return []


