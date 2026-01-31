import os
import sys
import time
import logging
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

from yfinance_client import YFinanceClient
from sheets_client import SheetsClient

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_target_tickers(all_tickers, master_df, limit=50):
    """
    업데이트 대상 티커를 선정합니다.
    1순위: Master Data에 없는 신규 티커
    2순위: Master Data에 있지만 Last_Updated가 오래된 티커
    """
    existing_tickers_set = set(master_df['Ticker'].unique()) if not master_df.empty else set()
    
    new_tickers = [t for t in all_tickers if t not in existing_tickers_set]
    
    existing_candidates_df = master_df[master_df['Ticker'].isin(all_tickers)].copy()
    
    if not existing_candidates_df.empty and 'Last_Updated' in existing_candidates_df.columns:
        existing_candidates_df['Last_Updated_Dt'] = pd.to_datetime(
            existing_candidates_df['Last_Updated'], errors='coerce'
        )
        existing_candidates_df['Last_Updated_Dt'] = existing_candidates_df['Last_Updated_Dt'].fillna(pd.Timestamp.min)
        
        existing_candidates_df.sort_values(by='Last_Updated_Dt', ascending=True, inplace=True)
        old_tickers = existing_candidates_df['Ticker'].tolist()
    else:
        old_tickers = [t for t in all_tickers if t in existing_tickers_set]

    targets = []
    targets.extend(new_tickers)
    
    remaining_slots = limit - len(targets)
    if remaining_slots > 0:
        targets.extend(old_tickers[:remaining_slots])
    
    return targets[:limit]

def main():
    load_dotenv()
    
    logger.info("Starting Financial Data Pipeline (Yahoo Finance)...")
    
    try:
        sheets_client = SheetsClient()
        yf_client = YFinanceClient()
        
        logger.info("Fetching all tickers from Google Sheets...")
        all_tickers = sheets_client.get_all_tickers(gid=0)
        logger.info(f"Found {len(all_tickers)} tickers in source list.")
        
        logger.info("Fetching existing Master Data...")
        master_df = sheets_client.get_master_data()
        logger.info(f"Loaded {len(master_df)} existing records.")
        
        targets = get_target_tickers(all_tickers, master_df, limit=50)
        logger.info(f"Selected {len(targets)} tickers for update.")
        
        if not targets:
            logger.info("No tickers to update. Exiting.")
            return

        updated_rows = []
        
        for i, ticker in enumerate(targets):
            logger.info(f"[{i+1}/{len(targets)}] Fetching data for {ticker}...")
            
            try:
                data = yf_client.get_financials(ticker)
                
                row = {
                    'Ticker': ticker,
                    'Last_Updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'Error_Log': ''
                }
                
                if data:
                    row.update(data)
                else:
                    row['Error_Log'] = 'No Data (Empty DataFrame)'
                
                updated_rows.append(row)
                
                # Yahoo Finance는 엄격한 Rate Limit은 없지만, 너무 빠르면 차단될 수 있음
                time.sleep(1.0) 
                
            except Exception as e:
                logger.error(f"Error processing {ticker}: {e}")
                row = {
                    'Ticker': ticker,
                    'Last_Updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'Error_Log': f"Exception: {str(e)}"
                }
                updated_rows.append(row)

        if updated_rows:
            logger.info(f"Updating Google Sheets with {len(updated_rows)} records...")
            sheets_client.update_master_data(updated_rows)
            logger.info("Update completed successfully.")
        else:
            logger.info("No data collected to update.")

    except Exception as e:
        logger.critical(f"Critical error in pipeline: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
