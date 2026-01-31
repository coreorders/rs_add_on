import requests

API_KEY = "vW4OApGlrXubZiA29EktP2h4lCGSDunI"
# 헤더는 여전히 유지 (안전하게)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def check(url):
    print(f"Testing: {url}")
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        print(f"Status: {r.status_code}")
        if r.status_code != 200:
            print(f"Error: {r.text[:100]}")
        else:
            print("Success!")
            print(f"Data length: {len(r.json())}")
    except Exception as e:
        print(f"Ex: {e}")
    print("-" * 20)

# 1. Stable endpoint with path parameter (Failed before)
# check(f"https://financialmodelingprep.com/stable/income-statement/AAPL?period=quarter&limit=5&apikey={API_KEY}")

# 2. Stable endpoint with Query Parameter (According to search result for PROFILE, maybe income-statement works similarly)
# Search result: https://financialmodelingprep.com/stable/income-statement?symbol=AAPL
check(f"https://financialmodelingprep.com/stable/income-statement?symbol=AAPL&period=quarter&limit=5&apikey={API_KEY}")

# 3. v3 with Query parameter? (Just in case)
check(f"https://financialmodelingprep.com/api/v3/income-statement?symbol=AAPL&period=quarter&limit=5&apikey={API_KEY}")
