import requests

API_KEY = "vW4OApGlrXubZiA29EktP2h4lCGSDunI"
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
    except Exception as e:
        print(f"Ex: {e}")
    print("-" * 20)

# v4 Income Statement
check(f"https://financialmodelingprep.com/api/v4/income-statement/AAPL?apikey={API_KEY}")

# v3 Balance Sheet (to see if broadly blocked)
check(f"https://financialmodelingprep.com/api/v3/balance-sheet-statement/AAPL?limit=5&apikey={API_KEY}")
