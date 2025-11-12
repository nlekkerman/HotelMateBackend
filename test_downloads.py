"""
Manual test script for PDF and Excel download endpoints.

This script tests both ID-based and date-based download methods
for stocktakes and periods.

Usage:
    python test_downloads.py

Requirements:
    - Django server running
    - Valid authentication token
    - Test data in database (stocktakes and periods)
"""

import requests
import os


# Configuration
BASE_URL = "http://localhost:8000"  # Change to your server URL
HOTEL_IDENTIFIER = "test-hotel"  # Change to your hotel slug/subdomain
AUTH_TOKEN = "your_token_here"  # Replace with valid token

# Test data
STOCKTAKE_ID = 1  # Replace with valid stocktake ID
PERIOD_ID = 1  # Replace with valid period ID
START_DATE = "2024-11-01"  # Replace with valid date
END_DATE = "2024-11-30"  # Replace with valid date

# Output directory
OUTPUT_DIR = "test_downloads_output"


def setup_output_dir():
    """Create output directory if it doesn't exist."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"✓ Created output directory: {OUTPUT_DIR}")


def get_headers():
    """Get request headers with authentication."""
    return {
        "Authorization": f"Token {AUTH_TOKEN}",
        "Accept": "*/*"
    }


def test_stocktake_pdf_by_id():
    """Test stocktake PDF download by ID."""
    print("\n" + "="*60)
    print("TEST: Stocktake PDF Download by ID")
    print("="*60)
    
    url = f"{BASE_URL}/api/stock-tracker/{HOTEL_IDENTIFIER}/stocktakes/{STOCKTAKE_ID}/download-pdf/"
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=get_headers())
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            filename = f"{OUTPUT_DIR}/stocktake_{STOCKTAKE_ID}_by_id.pdf"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"✓ SUCCESS: Downloaded to {filename}")
            print(f"  File size: {len(response.content)} bytes")
            print(f"  Content-Type: {response.headers.get('Content-Type')}")
        else:
            print(f"✗ FAILED: {response.text}")
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")


def test_stocktake_pdf_by_date():
    """Test stocktake PDF download by date range."""
    print("\n" + "="*60)
    print("TEST: Stocktake PDF Download by Date Range")
    print("="*60)
    
    url = f"{BASE_URL}/api/stock-tracker/{HOTEL_IDENTIFIER}/stocktakes/download-pdf/?start_date={START_DATE}&end_date={END_DATE}"
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=get_headers())
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            filename = f"{OUTPUT_DIR}/stocktake_{START_DATE}_to_{END_DATE}_by_date.pdf"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"✓ SUCCESS: Downloaded to {filename}")
            print(f"  File size: {len(response.content)} bytes")
            print(f"  Content-Type: {response.headers.get('Content-Type')}")
        else:
            print(f"✗ FAILED: {response.text}")
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")


def test_stocktake_excel_by_id():
    """Test stocktake Excel download by ID."""
    print("\n" + "="*60)
    print("TEST: Stocktake Excel Download by ID")
    print("="*60)
    
    url = f"{BASE_URL}/api/stock-tracker/{HOTEL_IDENTIFIER}/stocktakes/{STOCKTAKE_ID}/download-excel/"
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=get_headers())
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            filename = f"{OUTPUT_DIR}/stocktake_{STOCKTAKE_ID}_by_id.xlsx"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"✓ SUCCESS: Downloaded to {filename}")
            print(f"  File size: {len(response.content)} bytes")
            print(f"  Content-Type: {response.headers.get('Content-Type')}")
        else:
            print(f"✗ FAILED: {response.text}")
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")


def test_stocktake_excel_by_date():
    """Test stocktake Excel download by date range."""
    print("\n" + "="*60)
    print("TEST: Stocktake Excel Download by Date Range")
    print("="*60)
    
    url = f"{BASE_URL}/api/stock-tracker/{HOTEL_IDENTIFIER}/stocktakes/download-excel/?start_date={START_DATE}&end_date={END_DATE}"
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=get_headers())
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            filename = f"{OUTPUT_DIR}/stocktake_{START_DATE}_to_{END_DATE}_by_date.xlsx"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"✓ SUCCESS: Downloaded to {filename}")
            print(f"  File size: {len(response.content)} bytes")
            print(f"  Content-Type: {response.headers.get('Content-Type')}")
        else:
            print(f"✗ FAILED: {response.text}")
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")


def test_period_pdf_by_id():
    """Test period PDF download by ID."""
    print("\n" + "="*60)
    print("TEST: Period PDF Download by ID")
    print("="*60)
    
    url = f"{BASE_URL}/api/stock-tracker/{HOTEL_IDENTIFIER}/periods/{PERIOD_ID}/download-pdf/"
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=get_headers())
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            filename = f"{OUTPUT_DIR}/period_{PERIOD_ID}_by_id.pdf"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"✓ SUCCESS: Downloaded to {filename}")
            print(f"  File size: {len(response.content)} bytes")
            print(f"  Content-Type: {response.headers.get('Content-Type')}")
        else:
            print(f"✗ FAILED: {response.text}")
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")


def test_period_pdf_by_date():
    """Test period PDF download by date range."""
    print("\n" + "="*60)
    print("TEST: Period PDF Download by Date Range")
    print("="*60)
    
    url = f"{BASE_URL}/api/stock-tracker/{HOTEL_IDENTIFIER}/periods/download-pdf/?start_date={START_DATE}&end_date={END_DATE}"
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=get_headers())
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            filename = f"{OUTPUT_DIR}/period_{START_DATE}_to_{END_DATE}_by_date.pdf"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"✓ SUCCESS: Downloaded to {filename}")
            print(f"  File size: {len(response.content)} bytes")
            print(f"  Content-Type: {response.headers.get('Content-Type')}")
        else:
            print(f"✗ FAILED: {response.text}")
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")


def test_period_excel_by_id():
    """Test period Excel download by ID."""
    print("\n" + "="*60)
    print("TEST: Period Excel Download by ID")
    print("="*60)
    
    url = f"{BASE_URL}/api/stock-tracker/{HOTEL_IDENTIFIER}/periods/{PERIOD_ID}/download-excel/"
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=get_headers())
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            filename = f"{OUTPUT_DIR}/period_{PERIOD_ID}_by_id.xlsx"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"✓ SUCCESS: Downloaded to {filename}")
            print(f"  File size: {len(response.content)} bytes")
            print(f"  Content-Type: {response.headers.get('Content-Type')}")
        else:
            print(f"✗ FAILED: {response.text}")
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")


def test_period_excel_by_date():
    """Test period Excel download by date range."""
    print("\n" + "="*60)
    print("TEST: Period Excel Download by Date Range")
    print("="*60)
    
    url = f"{BASE_URL}/api/stock-tracker/{HOTEL_IDENTIFIER}/periods/download-excel/?start_date={START_DATE}&end_date={END_DATE}"
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=get_headers())
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            filename = f"{OUTPUT_DIR}/period_{START_DATE}_to_{END_DATE}_by_date.xlsx"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"✓ SUCCESS: Downloaded to {filename}")
            print(f"  File size: {len(response.content)} bytes")
            print(f"  Content-Type: {response.headers.get('Content-Type')}")
        else:
            print(f"✗ FAILED: {response.text}")
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")


def test_period_pdf_without_cocktails():
    """Test period PDF download without cocktails."""
    print("\n" + "="*60)
    print("TEST: Period PDF Download by ID (without cocktails)")
    print("="*60)
    
    url = f"{BASE_URL}/api/stock-tracker/{HOTEL_IDENTIFIER}/periods/{PERIOD_ID}/download-pdf/?include_cocktails=false"
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=get_headers())
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            filename = f"{OUTPUT_DIR}/period_{PERIOD_ID}_no_cocktails.pdf"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"✓ SUCCESS: Downloaded to {filename}")
            print(f"  File size: {len(response.content)} bytes")
        else:
            print(f"✗ FAILED: {response.text}")
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")


def test_combined_report_by_id():
    """Test combined stocktake + period PDF download by ID."""
    print("\n" + "="*60)
    print("TEST: Combined Report PDF Download by ID")
    print("="*60)
    
    url = f"{BASE_URL}/api/stock-tracker/{HOTEL_IDENTIFIER}/stocktakes/{STOCKTAKE_ID}/download-combined-pdf/"
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=get_headers())
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            filename = f"{OUTPUT_DIR}/combined_report_{STOCKTAKE_ID}_by_id.pdf"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"✓ SUCCESS: Downloaded to {filename}")
            print(f"  File size: {len(response.content)} bytes")
            print(f"  Content-Type: {response.headers.get('Content-Type')}")
            print("  ✓ This PDF contains BOTH stocktake AND period data!")
        else:
            print(f"✗ FAILED: {response.text}")
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")


def test_combined_report_by_date():
    """Test combined stocktake + period PDF download by date range."""
    print("\n" + "="*60)
    print("TEST: Combined Report PDF Download by Date Range")
    print("="*60)
    
    url = f"{BASE_URL}/api/stock-tracker/{HOTEL_IDENTIFIER}/stocktakes/download-combined-pdf/?start_date={START_DATE}&end_date={END_DATE}"
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=get_headers())
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            filename = f"{OUTPUT_DIR}/combined_report_{START_DATE}_to_{END_DATE}_by_date.pdf"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"✓ SUCCESS: Downloaded to {filename}")
            print(f"  File size: {len(response.content)} bytes")
            print(f"  Content-Type: {response.headers.get('Content-Type')}")
            print("  ✓ This PDF contains BOTH stocktake AND period data!")
        else:
            print(f"✗ FAILED: {response.text}")
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")


def test_error_cases():
    """Test error handling."""
    print("\n" + "="*60)
    print("TEST: Error Handling")
    print("="*60)
    
    # Test 1: Missing date parameters
    print("\n1. Missing end_date parameter:")
    url = f"{BASE_URL}/api/stock-tracker/{HOTEL_IDENTIFIER}/stocktakes/download-pdf/?start_date={START_DATE}"
    response = requests.get(url, headers=get_headers())
    print(f"   Status: {response.status_code} (Expected: 400)")
    if response.status_code == 400:
        print(f"   ✓ Correct error response")
    
    # Test 2: Invalid date format
    print("\n2. Invalid date format:")
    url = f"{BASE_URL}/api/stock-tracker/{HOTEL_IDENTIFIER}/stocktakes/download-pdf/?start_date=2024/11/01&end_date=2024/11/30"
    response = requests.get(url, headers=get_headers())
    print(f"   Status: {response.status_code} (Expected: 400)")
    if response.status_code == 400:
        print(f"   ✓ Correct error response")
    
    # Test 3: Non-existent date range
    print("\n3. Non-existent date range:")
    url = f"{BASE_URL}/api/stock-tracker/{HOTEL_IDENTIFIER}/stocktakes/download-pdf/?start_date=2025-12-01&end_date=2025-12-31"
    response = requests.get(url, headers=get_headers())
    print(f"   Status: {response.status_code} (Expected: 404)")
    if response.status_code == 404:
        print(f"   ✓ Correct error response")


def print_summary():
    """Print test summary."""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Output directory: {OUTPUT_DIR}")
    print("\nTests completed! Check the output directory for downloaded files.")
    print("\nTo verify the downloads:")
    print("  1. Check that PDF files open correctly")
    print("  2. Check that Excel files open correctly")
    print("  3. Verify content matches expected data")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("DOWNLOAD ENDPOINTS TEST SUITE")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"Hotel: {HOTEL_IDENTIFIER}")
    print(f"Stocktake ID: {STOCKTAKE_ID}")
    print(f"Period ID: {PERIOD_ID}")
    print(f"Date Range: {START_DATE} to {END_DATE}")
    print("="*60)
    
    # Check configuration
    if AUTH_TOKEN == "your_token_here":
        print("\n⚠ WARNING: Please set AUTH_TOKEN in the script before running!")
        print("You can get your token from the Django admin or API login.")
        return
    
    # Setup
    setup_output_dir()
    
    # Run tests
    test_stocktake_pdf_by_id()
    test_stocktake_pdf_by_date()
    test_stocktake_excel_by_id()
    test_stocktake_excel_by_date()
    test_period_pdf_by_id()
    test_period_pdf_by_date()
    test_period_excel_by_id()
    test_period_excel_by_date()
    test_period_pdf_without_cocktails()
    test_combined_report_by_id()  # NEW: Combined report
    test_combined_report_by_date()  # NEW: Combined report by date
    test_error_cases()
    
    # Summary
    print_summary()


if __name__ == "__main__":
    main()
