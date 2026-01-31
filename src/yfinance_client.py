import yfinance as yf
import pandas as pd
import math

class YFinanceClient:
    def __init__(self):
        # API Key 불필요
        pass

    def get_financials(self, ticker_symbol):
        """
        특정 티커의 분기별 재무 데이터를 가져옵니다.
        Revenue: Total Revenue
        EPS: Diluted EPS
        """
        try:
            ticker = yf.Ticker(ticker_symbol)
            # quarterly_financials 가져오기 (Index: 항목명, Columns: 날짜)
            qf = ticker.quarterly_financials
            
            # DataFrame이 비어있으면 None 반환
            if qf.empty:
                return None
                
            # 데이터 전처리: 날짜 내림차순 정렬 (최신이 왼쪽/0번 인덱스)
            # yfinance는 보통 최신이 왼쪽이지만 확실하게 하기 위해 Transpose -> Sort -> Transpose 할 수도 있고, 
            # 단순히 컬럼을 Sorting 할 수도 있음.
            # qf.columns는 DatetimeIndex
            sorted_cols = sorted(qf.columns, reverse=True)
            qf = qf[sorted_cols]
            
            # 최근 8분기 확보 (YoY 계산을 위해 최소 5분기, 최대 8분기 필요)
            recent_cols = sorted_cols[:8]
            
            # 결과 딕셔너리 초기화 (Revenue, EPS 1~8)
            result = {}
            for i in range(1, 9):
                result[f'Q{i}_Revenue'] = 0
                result[f'Q{i}_EPS'] = 0.0
            
            # YoY 성장률 초기화 (1~4)
            for i in range(1, 5):
                result[f'Q{i}_Rev_YoY'] = 0.0
                result[f'Q{i}_EPS_YoY'] = 0.0

            # 데이터 채우기
            for i, date_col in enumerate(recent_cols):
                idx = i + 1 # 1-based index (Q1 being most recent)
                
                # Revenue
                try:
                    rev = qf.loc['Total Revenue', date_col]
                    if pd.isna(rev): rev = 0
                except KeyError:
                    try:
                        rev = qf.loc['Operating Revenue', date_col]
                        if pd.isna(rev): rev = 0
                    except KeyError:
                        rev = 0
                
                # EPS
                try:
                    eps = qf.loc['Diluted EPS', date_col]
                    if pd.isna(eps): eps = 0.0
                except KeyError:
                    try:
                        eps = qf.loc['Basic EPS', date_col]
                        if pd.isna(eps): eps = 0.0
                    except KeyError:
                        eps = 0.0
                
                result[f'Q{idx}_Revenue'] = float(rev)
                result[f'Q{idx}_EPS'] = float(eps)

            # YoY 성장률 계산 (Q1 vs Q5, Q2 vs Q6, ...)
            # 데이터가 충분한지 확인해가며 계산
            for i in range(1, 5):
                curr_idx = i      # Q1, Q2, Q3, Q4
                prev_idx = i + 4  # Q5, Q6, Q7, Q8 (1년 전)
                
                # 전년 동기 데이터가 존재하는지 확인 (fetched length check)
                if len(recent_cols) >= prev_idx:
                    # Revenue YoY
                    curr_rev = result[f'Q{curr_idx}_Revenue']
                    prev_rev = result[f'Q{prev_idx}_Revenue']
                    if prev_rev != 0:
                        result[f'Q{curr_idx}_Rev_YoY'] = (curr_rev - prev_rev) / abs(prev_rev)
                    
                    # EPS YoY
                    curr_eps = result[f'Q{curr_idx}_EPS']
                    prev_eps = result[f'Q{prev_idx}_EPS']
                    if prev_eps != 0:
                        result[f'Q{curr_idx}_EPS_YoY'] = (curr_eps - prev_eps) / abs(prev_eps)

            return result

        except Exception as e:
            print(f"Error fetching data for {ticker_symbol}: {e}")
            return None

if __name__ == "__main__":
    client = YFinanceClient()
    print(client.get_financials("AAPL"))
