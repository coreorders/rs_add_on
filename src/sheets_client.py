import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime

class SheetsClient:
    def __init__(self, spreadsheet_id=None):
        self.spreadsheet_id = spreadsheet_id or os.getenv("SPREADSHEET_ID")
        self.credentials_path = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH", "credentials.json")
        
        if not self.spreadsheet_id:
            raise ValueError("SPREADSHEET_ID is not set.")
            
        self.scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        self.client = self._authenticate()
        self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)

    def _authenticate(self):
        if not os.path.exists(self.credentials_path):
             # JSON 내용을 환경변수에서 직접 읽는 로직은 복잡해지므로 일단 파일 경로 우선
             # 실제 프로덕션(GitHub Actions)에서는 Secrets를 파일로 덤프해서 사용 예정
             raise FileNotFoundError(f"Credentials file not found at: {self.credentials_path}")
        
        creds = ServiceAccountCredentials.from_json_keyfile_name(self.credentials_path, self.scope)
        return gspread.authorize(creds)

    def get_worksheet_by_id(self, gid):
        """GID를 사용하여 워크시트를 가져옵니다."""
        for worksheet in self.spreadsheet.worksheets():
            if str(worksheet.id) == str(gid):
                return worksheet
        raise ValueError(f"Worksheet with GID {gid} not found.")

    def get_all_tickers(self, gid=0):
        """Ticker List 시트(기본 gid=0)에서 모든 티커를 가져옵니다."""
        worksheet = self.get_worksheet_by_id(gid)
        # 첫 번째 컬럼을 티커 목록으로 가정
        tickers = worksheet.col_values(1)
        # 헤더가 있을 수 있으므로 첫 줄이 'Ticker' 같은 텍스트라면 제외하는 등의 로직 필요
        # 여기서는 단순히 읽어오고 호출부에서 처리하도록 하거나, 
        # Ticker List가 그냥 리스트만 있다고 가정
        if tickers and tickers[0].lower() == 'ticker':
            tickers = tickers[1:]
        
        # 빈 문자열 제거 및 중복 제거
        return list(set([t.strip() for t in tickers if t.strip()]))

    def get_master_data(self, gid=1101703314):
        """Master Data 시트 데이터를 DataFrame으로 가져옵니다."""
        worksheet = self.get_worksheet_by_id(gid)
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        # 필수 컬럼이 없는 빈 시트인 경우 처리
        if df.empty and 'Ticker' not in df.columns:
            # 컬럼 정의 (빈 프레임) - 여기서는 최소한의 고정 컬럼만 반환
            columns = ['Ticker', 'Last_Updated', 'Error_Log']
            return pd.DataFrame(columns=columns)
            
        return df

    def update_master_data(self, new_data_list, gid=1101703314):
        """
        Master Data 시트를 업데이트합니다. (동적 컬럼 방식)
        """
        worksheet = self.get_worksheet_by_id(gid)
        
        # 1. 기존 데이터 로드
        existing_records = worksheet.get_all_records()
        if existing_records:
            df_old = pd.DataFrame(existing_records)
            # Ticker 컬럼이 있는지 확인
            if 'Ticker' in df_old.columns:
                df_old.set_index('Ticker', inplace=True)
            else:
                 # 비정상 상태면 초기화
                 df_old = pd.DataFrame()
        else:
            df_old = pd.DataFrame()

        # 2. 새로운 데이터 준비
        df_new = pd.DataFrame(new_data_list)
        if df_new.empty:
            return
        df_new.set_index('Ticker', inplace=True)

        # 3. 컬럼 통합 (동적 컬럼)
        # 고정 컬럼
        fixed_cols = ['Last_Updated', 'Error_Log']
        
        # 동적 컬럼 (Rev_, EPS_, YoY_ 로 시작하는 것들) 추출
        # df_old와 df_new의 모든 컬럼을 합침
        all_cols = set()
        if not df_old.empty:
            all_cols.update(df_old.columns)
        all_cols.update(df_new.columns)
        
        # 날짜 컬럼만 필터링 및 정렬
        date_cols = [c for c in all_cols if c not in fixed_cols and c != 'Ticker']
        
        # 정렬 로직: 날짜 부분(YYYY-MM-DD)을 추출해서 내림차순(최신이 왼쪽) 정렬
        # 예: Rev_2025-12-31 -> 2025-12-31
        def sort_key(col_name):
            # 접두사 분리 (Rev_, EPS_, YoY_Rev_, YoY_EPS_)
            # 단순히 뒤에서 10자리(YYYY-MM-DD) 추출
            if len(col_name) >= 10:
                date_part = col_name[-10:]
                prefix = col_name[:-10]
                # 정렬 우선순위: 날짜(내림차순) -> 항목(Revenue, EPS, YoY...)
                return (date_part, prefix)
            return ("", col_name)

        # 복합 정렬: 날짜 내림차순
        date_cols.sort(key=lambda x: sort_key(x), reverse=True)

        # 최종 컬럼 순서: Ticker(인덱스) + Fixed + Dynamic(Sorted)
        # Last_Updated는 맨 앞에, Error_Log는 맨 뒤에
        final_column_order = ['Last_Updated'] + date_cols + ['Error_Log']
        
        # 4. 데이터 병합
        if df_old.empty:
            final_df = df_new
        else:
            # 먼저 인덱스 합치기
            all_index = df_old.index.union(df_new.index)
            final_df = pd.DataFrame(index=all_index)
            
            # 각 컬럼별로 처리
            for col in final_column_order:
                old_series = df_old[col] if col in df_old.columns else pd.Series(index=all_index)
                new_series = df_new[col] if col in df_new.columns else pd.Series(index=all_index)
                
                # 병합 로직: Old 값 우선, 단 Old가 0/NaN/Empty면 New 값 사용
                merged = old_series.copy()
                
                # reindex
                merged = merged.reindex(all_index)
                new_val = new_series.reindex(all_index)
                
                # 마스크 생성: (isna) | (== 0) | (== '')
                # 숫자 변환 시도 (문자열 빈칸 처리 위해)
                merged_numeric = pd.to_numeric(merged, errors='coerce').fillna(0)
                
                # Last_Updated는 무조건 New가 있으면 New로
                if col == 'Last_Updated':
                     final_df[col] = new_val.combine_first(merged)
                else:
                    # 일반 데이터: 0인 곳만 update
                    update_mask = (merged_numeric == 0)
                    # where(cond, other): cond가 True면 유지, False면 other 사용
                    # 우리는 mask가 True(0임)일 때 new_val을 쓰고 싶음 -> cond는 ~mask
                    final_df[col] = merged.where(~update_mask, new_val)

        # 5. 마무리 및 저장
        final_df.fillna('', inplace=True) # NaN -> 빈 문자열 (0대신 깔끔하게)
        final_df.reset_index(inplace=True) # Ticker 복구
        
        # 컬럼 순서 강제 적용 (없는 컬럼은 빈 값으로 추가)
        for col in final_column_order:
            if col not in final_df.columns:
                final_df[col] = ''
                
        # Ticker + final_column_order
        final_output_cols = ['Ticker'] + final_column_order
        final_df = final_df[final_output_cols]
        
        # 값 리스트 변환 (NaN 방지)
        final_df = final_df.fillna('')
        
        data_to_write = [final_df.columns.tolist()] + final_df.values.tolist()
        
        worksheet.clear()
        worksheet.update(data_to_write)
