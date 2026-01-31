import requests
import os

API_KEY = "vW4OApGlrXubZiA29EktP2h4lCGSDunI"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def test_url(name, url):
    print(f"--- Testing {name} ---")
    print(f"URL: {url}")
    try:
        # 1. Without Headers
        print("1. Request WITHOUT custom headers...")
        r = requests.get(url, timeout=5)
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            print("   Success!")
        else:
            print(f"   Failed: {r.text[:100]}")

        # 2. With Headers
        print("2. Request WITH User-Agent header...")
        r = requests.get(url, headers=HEADERS, timeout=5)
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            print("   Success!")
        else:
            print(f"   Failed: {r.text[:100]}")
            
    except Exception as e:
        print(f"   Exception: {e}")
    print("\n")

if __name__ == "__main__":
    # Test 1: User's successful example (Profile)
    test_url("User's Example (Profile)", f"https://financialmodelingprep.com/stable/profile?symbol=AAPL&apikey={API_KEY}")
    
    # Test 2: Project Endpoint (Income Statement)
    test_url("Project Endpoint (Income Statement)", f"https://financialmodelingprep.com/api/v3/income-statement/AAPL?period=quarter&limit=5&apikey={API_KEY}")
