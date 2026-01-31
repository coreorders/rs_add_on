import yfinance as yf
import pandas as pd
import math

class YFinanceClient:
    def __init__(self):
        # API Key 불필요
        pass

    def get_financials(self, ticker_symbol):
        """
        특정 티커의 분기별 재무 데이터를 가져옵니다. (동적 날짜 컬럼)
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
            sorted_cols = sorted(qf.columns, reverse=True)
            qf = qf[sorted_cols]
            
            # 반환할 결과 딕셔너리
            result = {}
            
            # 모든 분기 데이터 순회
            for date_col in qf.columns:
                # 날짜 포맷 (YYYY-MM-DD)
                date_str = date_col.strftime('%Y-%m-%d')
                
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
                
                # 키 포맷: Rev_YYYY-MM-DD, EPS_YYYY-MM-DD
                result[f'Rev_{date_str}'] = float(rev)
                result[f'EPS_{date_str}'] = float(eps)
                
            # YoY 성장률 계산 로직 제거 (User Request)
            # Revenue, EPS 데이터만 반환합니다.

            return result

        except Exception as e:
            print(f"Error fetching data for {ticker_symbol}: {e}")
            return None

if __name__ == "__main__":
    client = YFinanceClient()
    print(client.get_financials("AAPL"))
