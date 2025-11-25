# End-to-End Test Script for MHC Cause List Application
# Tests all major functionality of the backend API

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "MHC Cause List Application - E2E Tests" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$baseUrl = "http://localhost:8000"
$testsPassed = 0
$testsFailed = 0

function Test-Endpoint {
    param(
        [string]$TestName,
        [scriptblock]$TestBlock
    )
    
    Write-Host "Testing: $TestName..." -ForegroundColor Yellow
    try {
        & $TestBlock
        Write-Host "✓ PASSED: $TestName`n" -ForegroundColor Green
        $script:testsPassed++
        return $true
    }
    catch {
        Write-Host "✗ FAILED: $TestName" -ForegroundColor Red
        Write-Host "  Error: $($_.Exception.Message)`n" -ForegroundColor Red
        $script:testsFailed++
        return $false
    }
}

# Test 1: Health Check
Test-Endpoint "Backend Health Check" {
    $response = Invoke-RestMethod -Uri "$baseUrl/health" -Method GET
    if ($response.status -ne "healthy") {
        throw "Health check failed"
    }
}

# Test 2: Root Endpoint
Test-Endpoint "Root API Endpoint" {
    $response = Invoke-RestMethod -Uri "$baseUrl/" -Method GET
    if (-not $response.message) {
        throw "Root endpoint returned unexpected response"
    }
}

# Test 3: User Registration (create test user)
Test-Endpoint "User Registration" {
    $timestamp = [DateTimeOffset]::Now.ToUnixTimeSeconds()
    $body = @{
        username = "testuser$timestamp"
        email = "test$timestamp@example.com"
        password = "testpassword123"
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/api/auth/register" -Method POST -Body $body -ContentType "application/json"
        if (-not $response.username) {
            throw "Registration failed"
        }
    }
    catch {
        # User might already exist, that's okay
        if ($_.Exception.Message -notlike "*already*") {
            throw $_
        }
    }
}

# Test 4: User Login
Test-Endpoint "User Authentication" {
    $body = 'username=admin&password=admin'
    $response = Invoke-RestMethod -Uri "$baseUrl/api/auth/token" -Method POST -Body $body -ContentType "application/x-www-form-urlencoded"
    if (-not $response.access_token) {
        throw "Login failed - no access token"
    }
    $script:authToken = $response.access_token
}

# Get authentication headers for subsequent tests
$authHeaders = @{ "Authorization" = "Bearer $authToken" }

# Test 5: Search All Cases
Test-Endpoint "Search All Cases" {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/cases/search" -Method GET -Headers $authHeaders
    if ($response.Count -eq 0) {
        throw "No cases found in database"
    }
    Write-Host "  Found $($response.Count) cases" -ForegroundColor Cyan
}

# Test 6: Search HRCE Cases
Test-Endpoint "Filter HRCE Cases" {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/cases/search?is_hrce=true" -Method GET -Headers $authHeaders
    if ($response.Count -eq 0) {
        throw "No HRCE cases found"
    }
    Write-Host "  Found $($response.Count) HRCE cases" -ForegroundColor Cyan
    foreach ($case in $response) {
        if (-not $case.is_hrce) {
            throw "Non-HRCE case returned in HRCE filter"
        }
    }
}

# Test 7: Search by Query
Test-Endpoint "Search by Text Query" {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/cases/search?query=temple" -Method GET -Headers $authHeaders
    if ($response.Count -eq 0) {
        throw "No temple cases found"
    }
    Write-Host "  Found $($response.Count) cases matching 'temple'" -ForegroundColor Cyan
}

# Test 8: Search by Advocate
Test-Endpoint "Search by Advocate Name" {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/cases/search?advocate=Krishnan" -Method GET -Headers $authHeaders
    if ($response.Count -eq 0) {
        throw "No cases found for advocate Krishnan"
    }
    Write-Host "  Found $($response.Count) cases for advocate Krishnan" -ForegroundColor Cyan
}

# Test 9: Get Case by ID
Test-Endpoint "Get Specific Case by ID" {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/cases/1" -Method GET -Headers $authHeaders
    if (-not $response.id -or $response.id -ne 1) {
        throw "Failed to retrieve case ID 1"
    }
    Write-Host "  Retrieved case: $($response.case_no)" -ForegroundColor Cyan
}

# Test 10: Get Related Cases
Test-Endpoint "Get Related Cases" {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/cases/1/related" -Method GET -Headers $authHeaders
    Write-Host "  Found $($response.Count) related cases" -ForegroundColor Cyan
}

# Test 11: Filter by Court Number
Test-Endpoint "Filter by Court Number" {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/cases/search?court_no=1" -Method GET -Headers $authHeaders
    if ($response.Count -eq 0) {
        throw "No cases found for court 1"
    }
    Write-Host "  Found $($response.Count) cases in Court No. 1" -ForegroundColor Cyan
}

# Test 12: Fuzzy Search
Test-Endpoint "Fuzzy Search with Typos" {
    $uri = $baseUrl + '/api/cases/search?petitioner=Ranganatha&fuzzy=true'
    $response = Invoke-RestMethod -Uri $uri -Method GET -Headers $authHeaders
    Write-Host "  Fuzzy search found $($response.Count) matches" -ForegroundColor Cyan
}

# Test 13: Scraper Status
Test-Endpoint "Get Scraper Status" {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/scraper/status" -Method GET -Headers $authHeaders
    if (-not $response.status) {
        throw "Scraper status endpoint failed"
    }
    Write-Host "  Scraper status: $($response.status)" -ForegroundColor Cyan
}

# Test 14: Get Scraper Logs (Admin only)
Test-Endpoint "Get Scraper Logs" {
    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/api/scraper/logs" -Method GET -Headers $authHeaders
        Write-Host "  Retrieved $($response.Count) scraper log entries" -ForegroundColor Cyan
    }
    catch {
        # If no logs exist yet, that's okay
        if ($_.Exception.Message -notlike "*404*") {
            throw $_
        }
        Write-Host "  No scraper logs yet (expected for new installation)" -ForegroundColor Cyan
    }
}

# Test 15: Frontend Availability
Test-Endpoint "Frontend Homepage" {
    $response = Invoke-WebRequest -Uri "http://localhost:5000" -Method GET
    if ($response.StatusCode -ne 200) {
        throw "Frontend not accessible"
    }
}

# Test 16: Frontend Search Page
Test-Endpoint "Frontend Search Page" {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/search" -Method GET
    if ($response.StatusCode -ne 200) {
        throw "Frontend search page not accessible"
    }
}

# Test 17: Frontend Admin Page
Test-Endpoint "Frontend Admin Page" {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/admin" -Method GET
    if ($response.StatusCode -ne 200) {
        throw "Frontend admin page not accessible"
    }
}

# Test 18: Frontend Login Page
Test-Endpoint "Frontend Login Page" {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/login" -Method GET
    if ($response.StatusCode -ne 200) {
        throw "Frontend login page not accessible"
    }
}

# Test 19: API Documentation
Test-Endpoint "API Documentation (Swagger)" {
    $response = Invoke-WebRequest -Uri "$baseUrl/docs" -Method GET
    if ($response.StatusCode -ne 200) {
        throw "API documentation not accessible"
    }
}

# Test 20: Date Range Filter
Test-Endpoint "Filter by Date Range" {
    $uri = $baseUrl + '/api/cases/search?hearing_date_from=2024-12-15&hearing_date_to=2024-12-20'
    $response = Invoke-RestMethod -Uri $uri -Method GET -Headers $authHeaders
    Write-Host "  Found $($response.Count) cases in date range" -ForegroundColor Cyan
}

# Display Results
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Test Results Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✓ Tests Passed: $testsPassed" -ForegroundColor Green
if ($testsFailed -gt 0) {
    Write-Host "✗ Tests Failed: $testsFailed" -ForegroundColor Red
} else {
    Write-Host "✗ Tests Failed: 0" -ForegroundColor Green
}
Write-Host "Total Tests: $($testsPassed + $testsFailed)" -ForegroundColor White

if ($testsFailed -eq 0) {
    Write-Host "`n🎉 ALL TESTS PASSED! Application is fully functional." -ForegroundColor Green
    Write-Host "`nYou can now access:" -ForegroundColor Cyan
    Write-Host "  • Frontend: http://localhost:5000" -ForegroundColor White
    Write-Host "  • Backend API: http://localhost:8000" -ForegroundColor White
    Write-Host "  • API Docs: http://localhost:8000/docs" -ForegroundColor White
    Write-Host "  • Admin Login: username=admin, password=admin" -ForegroundColor White
} else {
    Write-Host "`n⚠️  Some tests failed. Please review the errors above." -ForegroundColor Yellow
}

Write-Host "`n========================================`n" -ForegroundColor Cyan
