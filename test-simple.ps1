# End-to-End Test Script for MHC Cause List Application
Write-Host ""
Write-Host "========================================"
Write-Host "MHC Cause List Application - E2E Tests"
Write-Host "========================================"
Write-Host ""

$baseUrl = "http://localhost:8000"
$frontendUrl = "http://localhost:5000"
$testsPassed = 0
$testsFailed = 0

# Test 1: Backend Health Check
Write-Host "Test 1: Backend Health Check..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/health" -Method GET
    if ($response.status -eq "healthy") {
        Write-Host "PASSED: Backend is healthy" -ForegroundColor Green
        $testsPassed++
    } else {
        throw "Unexpected status"
    }
} catch {
    Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Test 2: User Login
Write-Host "Test 2: User Authentication..." -ForegroundColor Yellow
try {
    $body = 'username=admin&password=admin'
    $response = Invoke-RestMethod -Uri "$baseUrl/api/auth/token" -Method POST -Body $body -ContentType "application/x-www-form-urlencoded"
    $authToken = $response.access_token
    if ($authToken) {
        Write-Host "PASSED: Successfully authenticated" -ForegroundColor Green
        $testsPassed++
    } else {
        throw "No access token received"
    }
} catch {
    Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
    Write-Host ""
    exit 1
}
Write-Host ""

$authHeaders = @{ "Authorization" = "Bearer $authToken" }

# Test 3: Search All Cases
Write-Host "Test 3: Search All Cases..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/cases/search" -Method GET -Headers $authHeaders
    $count = $response.Count
    if ($count -gt 0) {
        Write-Host "PASSED: Found $count cases" -ForegroundColor Green
        $testsPassed++
    } else {
        throw "No cases found"
    }
} catch {
    Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Test 4: Filter HRCE Cases
Write-Host "Test 4: Filter HRCE Cases..." -ForegroundColor Yellow
try {
    $uri = "$baseUrl/api/cases/search?is_hrce=true"
    $response = Invoke-RestMethod -Uri $uri -Method GET -Headers $authHeaders
    $count = $response.Count
    if ($count -gt 0) {
        Write-Host "PASSED: Found $count HRCE cases" -ForegroundColor Green
        $testsPassed++
    } else {
        throw "No HRCE cases found"
    }
} catch {
    Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Test 5: Search by Query
Write-Host "Test 5: Search by Query (temple)..." -ForegroundColor Yellow
try {
    $uri = "$baseUrl/api/cases/search?query=temple"
    $response = Invoke-RestMethod -Uri $uri -Method GET -Headers $authHeaders
    $count = $response.Count
    if ($count -gt 0) {
        Write-Host "PASSED: Found $count cases matching 'temple'" -ForegroundColor Green
        $testsPassed++
    } else {
        throw "No temple cases found"
    }
} catch {
    Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Test 6: Get Case by ID
Write-Host "Test 6: Get Case by ID..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/cases/1" -Method GET -Headers $authHeaders
    if ($response.id -eq 1) {
        Write-Host "PASSED: Retrieved case $($response.case_no)" -ForegroundColor Green
        $testsPassed++
    } else {
        throw "Failed to retrieve case"
    }
} catch {
    Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Test 7: Get Related Cases
Write-Host "Test 7: Get Related Cases..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/cases/1/related" -Method GET -Headers $authHeaders
    Write-Host "PASSED: Found $($response.Count) related cases" -ForegroundColor Green
    $testsPassed++
} catch {
    Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Test 8: Scraper Status
Write-Host "Test 8: Get Scraper Status..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/scraper/status" -Method GET -Headers $authHeaders
    Write-Host "PASSED: Scraper status is $($response.status)" -ForegroundColor Green
    $testsPassed++
} catch {
    Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Test 9: Frontend Homepage
Write-Host "Test 9: Frontend Homepage..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri $frontendUrl -Method GET
    if ($response.StatusCode -eq 200) {
        Write-Host "PASSED: Frontend is accessible" -ForegroundColor Green
        $testsPassed++
    } else {
        throw "Unexpected status code"
    }
} catch {
    Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Test 10: API Documentation
Write-Host "Test 10: API Documentation..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/docs" -Method GET
    if ($response.StatusCode -eq 200) {
        Write-Host "PASSED: API docs accessible" -ForegroundColor Green
        $testsPassed++
    } else {
        throw "Unexpected status code"
    }
} catch {
    Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Display Results
Write-Host "========================================"
Write-Host "Test Results Summary"
Write-Host "========================================"
Write-Host "Tests Passed: $testsPassed" -ForegroundColor Green
if ($testsFailed -gt 0) {
    Write-Host "Tests Failed: $testsFailed" -ForegroundColor Red
} else {
    Write-Host "Tests Failed: 0" -ForegroundColor Green
}
Write-Host "Total Tests: $($testsPassed + $testsFailed)"
Write-Host ""

if ($testsFailed -eq 0) {
    Write-Host "ALL TESTS PASSED! Application is fully functional." -ForegroundColor Green
    Write-Host ""
    Write-Host "You can now access:" -ForegroundColor Cyan
    Write-Host "  Frontend: http://localhost:5000"
    Write-Host "  Backend API: http://localhost:8000"
    Write-Host "  API Docs: http://localhost:8000/docs"
    Write-Host "  Admin Login: username=admin, password=admin"
} else {
    Write-Host "Some tests failed. Please review the errors above." -ForegroundColor Yellow
}
Write-Host ""
Write-Host "========================================"
Write-Host ""
