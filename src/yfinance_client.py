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
            
            # 최근 4분기 확보 (미래 예측치가 포함될 수도 있으니 주의. yfinance는 보통 확정치만 줌)
            recent_cols = sorted_cols[:4]
            
            result = {
                'Q1_Revenue': 0, 'Q2_Revenue': 0, 'Q3_Revenue': 0, 'Q4_Revenue': 0,
                'Q1_EPS': 0.0, 'Q2_EPS': 0.0, 'Q3_EPS': 0.0, 'Q4_EPS': 0.0,
                'Revenue_Growth': 0.0,
                'EPS_Growth': 0.0
            }
            
            for i, date_col in enumerate(recent_cols):
                idx = i + 1
                # 값 가져오기 (없으면 0 처리)
                # Revenue
                try:
                    rev = qf.loc['Total Revenue', date_col]
                    if pd.isna(rev): rev = 0
                except KeyError:
                    # Total Revenue가 없으면 Operating Revenue 시도
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

            # 증감률 계산 (Q1 vs Q2 - 즉 최근분기 vs 직전분기 QoQ)
            # yfinance 데이터가 충분히(최소 2개) 있는지 확인
            if len(recent_cols) >= 2:
                rev_q1 = result['Q1_Revenue']
                rev_q2 = result['Q2_Revenue']
                if rev_q2 != 0:
                    result['Revenue_Growth'] = (rev_q1 - rev_q2) / abs(rev_q2)
                
                eps_q1 = result['Q1_EPS']
                eps_q2 = result['Q2_EPS']
                if eps_q2 != 0:
                    result['EPS_Growth'] = (eps_q1 - eps_q2) / abs(eps_q2)

            return result

        except Exception as e:
            print(f"Error fetching data for {ticker_symbol}: {e}")
            return None

if __name__ == "__main__":
    client = YFinanceClient()
    print(client.get_financials("AAPL"))
