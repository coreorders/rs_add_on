import yfinance as yf
import pandas as pd

def probe_ticker(ticker_symbol):
    print(f"--- Probing {ticker_symbol} ---")
    ticker = yf.Ticker(ticker_symbol)
    
    # Quarterly Income Statement
    # Note: different versions of yfinance might have different attributes
    # usually it is .quarterly_income_stmt or .quarterly_financials
    
    print("Fetching quarterly_financials...")
    try:
        qf = ticker.quarterly_financials
        print("Columns (Dates):", qf.columns)
        print("Index (Rows):", qf.index)
        
        # Check specific rows for Revenue and EPS
        # Revenue is often 'Total Revenue'
        # EPS is often 'Diluted EPS' or 'Basic EPS'
        
        print("\n[Possible Revenue Rows]")
        for idx in qf.index:
            if 'Revenue' in str(idx):
                print(f" - {idx}")
                
        print("\n[Possible EPS Rows]")
        for idx in qf.index:
            if 'EPS' in str(idx):
                print(f" - {idx}")
                
        # Print first few columns of data
        print("\n[Data Snippet]")
        print(qf.iloc[:, :2])
        
    except Exception as e:
        print(f"Error fetching financials: {e}")

if __name__ == "__main__":
    probe_ticker("AAPL")
