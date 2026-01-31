# Financial Data Pipeline (Yahoo Finance Add-on)

이 프로젝트는 **Yahoo Finance**에서 재무 데이터(매출, EPS)를 자동으로 수집하여 **Google Sheets**에 저장하는 자동화 파이프라인입니다.

## 🚀 주요 기능

1.  **자동 데이터 수집**
    *   Google Sheets에 있는 티커 목록을 읽어와서, Yahoo Finance에서 최신 분기 실적을 가져옵니다.
    *   **항목**: `Revenue` (매출), `EPS` (주당순이익)
    *   금융/은행권 기업(Revenue가 없는 경우)을 위해 `Operating Revenue`, `Interest Income` 등을 자동으로 찾아냅니다.

2.  **동적 날짜 컬럼 (Dynamic Columns)**
    *   고정된 분기(Q1, Q2...)가 아닌 **실제 발표 날짜(YYYY-MM-DD)**를 컬럼명으로 사용합니다.
    *   예: `Rev_2025-12-31`, `EPS_2025-12-31`
    *   새로운 분기 실적이 발표되면 **자동으로 새 날짜 컬럼이 추가**됩니다.
    *   시간이 지나도 과거 데이터가 삭제되지 않고 오른쪽으로 밀리며 계속 **누적(Accumulate)**됩니다.

3.  **스마트 업데이트 스케줄**
    *   **주기**: 매 시간 55분마다 실행 (`55 * * * *`)
    *   **처리량**: 회당 **50개** 티커 처리 (하루 최대 1,200개 커버)
    *   **우선순위**:
        1.  새로 추가된 신규 티커
        2.  업데이트한 지 가장 오래된 티커
    *   기존 데이터가 있는 경우 덮어쓰지 않고 유지하며, 빈 값(`0` 또는 `Empty`)인 경우에만 채워 넣습니다.

## 🛠️ 설치 및 설정 (Setup)

### 1. 로컬 환경 설정
Python 3.9 이상이 필요합니다.

```bash
# 의존성 패키지 설치
pip install -r requirements.txt
```

`.env` 파일을 생성하고 다음 내용을 추가합니다. (로컬 실행 시 필요)

```ini
SPREADSHEET_ID=your_google_sheet_id_here
GOOGLE_SHEETS_CREDENTIALS_PATH=credentials.json
```

### 2. Google Cloud Service Account
Google Sheets API를 사용하기 위해 서비스 계정 키(`credentials.json`)가 필요합니다.
1.  Google Cloud Console에서 프로젝트 생성 및 Sheets API 활성화.
2.  Service Account 생성 및 키(JSON) 다운로드.
3.  해당 서비스 계정 이메일(`xxx@xxx.iam.gserviceaccount.com`)을 구글 시트에 **'편집자'** 권한으로 초대(공유).

### 3. GitHub Actions (자동화)
이 저장소는 GitHub Actions를 통해 자동으로 실행됩니다.
GitHub Repository의 **Settings -> Secrets and variables -> Actions**에 다음 비밀 변수를 등록해야 합니다.

| Secret Name | 설명 |
| :--- | :--- |
| `SPREADSHEET_ID` | 대상 구글 시트의 ID (URL에 있는 긴 문자열) |
| `GOOGLE_SHEETS_CREDENTIALS` | `credentials.json` 파일의 **내용 전체**를 텍스트로 복사해서 붙여넣기 |

## 📊 시트 데이터 구조

데이터는 다음과 같이 보입니다. 최신 날짜가 항상 왼쪽(`Last_Updated` 옆)에 생성됩니다.

| Ticker | Last_Updated | Rev_2025-12-31 | EPS_2025-12-31 | ... | Rev_2024-09-30 | ... |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| AAPL | 2026-01-31... | 120,000,000 | 2.15 | ... | 95,000,000 | ... |
| CACC | 2026-01-31... | 500,000,000 | 10.5 | ... | ... | ... |

*   **Last_Updated**: 해당 티커를 마지막으로 크롤링한 시간 (한국 시간 기준 아님, 서버 시간)
*   **Error_Log**: 데이터 수집 실패 시 에러 메시지 기록

---
**Note**: 이 봇은 GitHub Actions의 무료 시간(2000분/월)을 사용합니다. 매시간 짧게 돌기 때문에 충분합니다.
