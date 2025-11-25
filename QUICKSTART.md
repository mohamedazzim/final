# Quick Start Guide - MHC Cause List Application

## 🚀 Current Status
✅ **Both servers are RUNNING**
- Backend: http://localhost:8000
- Frontend: http://localhost:5000

## 🔐 Login Credentials
- **Username:** admin
- **Password:** admin

## 🌐 Access Points

### User Interfaces
- **Homepage:** http://localhost:5000
- **Search Cases:** http://localhost:5000/search
- **Admin Dashboard:** http://localhost:5000/admin
- **Login Page:** http://localhost:5000/login

### API Endpoints
- **Health Check:** http://localhost:8000/health
- **API Docs (Swagger):** http://localhost:8000/docs
- **API Docs (ReDoc):** http://localhost:8000/redoc
- **Search Cases:** http://localhost:8000/api/cases/search
- **Get Case by ID:** http://localhost:8000/api/cases/{id}
- **Login:** http://localhost:8000/api/auth/token
- **Scraper Status:** http://localhost:8000/api/scraper/status

## 📊 Sample Data
The database contains 10 sample cases:
- 5 HRCE cases (temple/religious cases)
- 5 Non-HRCE cases (civil/criminal cases)
- Courts: 1, 2, 3, 4
- Date range: Dec 15-24, 2024

## 🧪 Run Tests
```powershell
.\test-simple.ps1
```

## 🛑 Stop Servers
```powershell
Get-Job | Stop-Job
Get-Job | Remove-Job
```

## ▶️ Start Servers Manually

### Backend
```powershell
cd backend
../.venv/Scripts/python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend
```powershell
cd frontend
npm run dev
```

## 📝 Key Features to Test

### Search Functionality
1. **Basic Search:** Search for "temple" or "HRCE"
2. **HRCE Filter:** Filter only HRCE cases
3. **Advocate Search:** Search by advocate name
4. **Court Filter:** Filter by court number
5. **Date Range:** Filter by hearing date range
6. **Fuzzy Search:** Try misspelled names

### Admin Features
1. **View Scraper Status:** Check last scraper run
2. **View Scraper Logs:** See scraping history
3. **Trigger Manual Scrape:** Run scraper on demand (requires admin role)

### Authentication
1. **Login:** Use admin/admin credentials
2. **Register:** Create new user account
3. **Protected Routes:** Access authenticated endpoints

## 🐛 Troubleshooting

### Backend Not Responding
```powershell
# Check if backend is running
Invoke-WebRequest -Uri http://localhost:8000/health
```

### Frontend Not Loading
```powershell
# Check if frontend is running
Invoke-WebRequest -Uri http://localhost:5000
```

### Database Issues
```powershell
# Re-seed the database
cd backend
../.venv/Scripts/python.exe seed_data.py
```

### Port Already in Use
```powershell
# Kill process on port 8000
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process

# Kill process on port 5000
Get-Process -Id (Get-NetTCPConnection -LocalPort 5000).OwningProcess | Stop-Process
```

## 📁 Important Files

### Configuration
- `backend/.env` - Database and secret key configuration
- `frontend/next.config.js` - Next.js configuration

### Database
- `mhc_causes.db` - SQLite database file

### Tests
- `test-simple.ps1` - End-to-end test script
- `TEST_RESULTS.md` - Detailed test results

## 🔄 Daily Automated Scraping
The backend is configured to automatically scrape new cause lists daily at 2:00 AM using APScheduler.

## 💡 Tips
- Use the Swagger UI at `/docs` for interactive API testing
- All API endpoints (except auth) require authentication
- HRCE cases are automatically identified by keywords
- Related cases are found using fuzzy string matching
- The admin user has full access to all features

## 📞 Support
For issues or questions, refer to:
- `TEST_RESULTS.md` - Full test report and setup details
- `replit.md` - Original project documentation
- API Docs at http://localhost:8000/docs
