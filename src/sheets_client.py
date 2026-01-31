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
            # 컬럼 정의 (빈 프레임)
            columns = [
                'Ticker', 'Last_Updated',
                'Q1_Revenue', 'Q2_Revenue', 'Q3_Revenue', 'Q4_Revenue',
                'Q1_EPS', 'Q2_EPS', 'Q3_EPS', 'Q4_EPS',
                'Revenue_Growth', 'EPS_Growth', 'Error_Log'
            ]
            return pd.DataFrame(columns=columns)
            
        return df

    def update_master_data(self, new_data_list, gid=1101703314):
        """
        Master Data 시트를 업데이트합니다.
        기존 데이터 보존 정책을 준수하며, 새로운 데이터로 덮어쓰거나 추가합니다.
        
        new_data_list: 업데이트할 딕셔너리 리스트 (키는 컬럼명과 일치해야 함)
        """
        worksheet = self.get_worksheet_by_id(gid)
        
        # 현재 데이터 로드
        existing_records = worksheet.get_all_records()
        
        # DataFrame으로 변환하여 병합 (Ticker 기준)
        if existing_records:
            df_old = pd.DataFrame(existing_records)
            # Ticker를 인덱스로 설정
            df_old.set_index('Ticker', inplace=True)
        else:
            df_old = pd.DataFrame()

        df_new = pd.DataFrame(new_data_list)
        if df_new.empty:
            return

        df_new.set_index('Ticker', inplace=True)
        
        # combine_first를 사용하여 업데이트 (df_new가 우선, 없으면 df_old 유지)
        # 하지만 우리는 덮어쓰기를 원하므로 update나 직접 병합 로직 사용
        # df_new에 있는 애들은 df_new 값으로, 나머지는 df_old 값 유지
        
        if df_old.empty:
            final_df = df_new
        else:
            # df_new의 컬럼들이 df_old에 없을 수도 있음 (새로운 컬럼이 추가된 경우?)
            # 여기서는 스키마가 고정되어 있다고 가정
            
            # update는 NaN이 아닌 값만 덮어씀. 우리는 일부러 비우는 경우는 없으므로 사용 가능
            # 하지만 Ticker가 df_old에 없는 경우 추가되어야 함.
            
            # 1. df_old 업데이트
            df_old.update(df_new)
            
            # 2. df_old에 없는 새로운 티커 추가
            new_tickers = df_new.index.difference(df_old.index)
            if not new_tickers.empty:
                df_to_add = df_new.loc[new_tickers]
                final_df = pd.concat([df_old, df_to_add])
            else:
                final_df = df_old

        # 인덱스 리셋 및 Ticker 컬럼 복구
        final_df.reset_index(inplace=True)
        
        # NaN 처리 (빈 문자열 등)
        final_df.fillna('', inplace=True)
        
        # Google Sheets에 다시 쓰기
        # 전체를 다시 쓰는 방식은 데이터가 많아지면 비효율적일 수 있으나,
        # 티커 수가 수천개 수준이면 괜찮음. 하루 200개 업데이트면 전체 로우 수는 몇천개 정도 예상.
        # 시트를 클리어하고 다시 씀. (컬럼 순서 유지 중요)
        
        columns = [
            'Ticker', 'Last_Updated',
            'Q1_Revenue', 'Q2_Revenue', 'Q3_Revenue', 'Q4_Revenue',
            'Q1_EPS', 'Q2_EPS', 'Q3_EPS', 'Q4_EPS',
            'Revenue_Growth', 'EPS_Growth', 'Error_Log'
        ]
        
        # 필요한 컬럼만 선택 및 순서 보장 (없는 컬럼은 추가)
        for col in columns:
            if col not in final_df.columns:
                final_df[col] = ''
        
        final_df = final_df[columns]
        
        # update operation
        # clear() 후 update하면 순간적으로 데이터가 사라지는 리스크가 있음.
        # 안전하게 하려면:
        # 1. 헤더 제외하고 데이터만 업데이트 (범위 지정)
        # 2. 행 개수가 늘어났으면 추가
        
        data_to_write = [final_df.columns.tolist()] + final_df.values.tolist()
        worksheet.clear()
        worksheet.update(data_to_write)
