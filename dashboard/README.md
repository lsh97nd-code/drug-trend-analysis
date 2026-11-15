# Dashboard 실행·배포 안내

이 Dashboard는 **HTML/CSS/JavaScript만 사용하는 정적 웹페이지**입니다. 공공데이터를 브라우저에서 시각화하므로 **AI API Key, 서버, 데이터베이스가 필요하지 않습니다.**

## 로컬 실행

`dashboard/index.html`을 브라우저로 직접 열거나, 프로젝트 루트에서:

```bash
python -m http.server 8000
```

브라우저에서 다음 주소로 접속합니다.

```text
http://localhost:8000/dashboard/
```

## 필터 기능

- 기간 빠른 선택: 전체 / 코로나 이전 / 유행·제약 / 이후
- 시작 월 / 종료 월 직접 선택
- 지표: 전체 / 향정신성의약품 / 대마 / 마약
- 12개월 이동평균 표시/숨김
- KPI: 기간, 데이터 포인트, 월평균, 최고 월
- 전년 동월 대비: 선택 기간의 각 월을 12개월 전 같은 월과 비교하는 증감률 차트
- 달력 월별 평균
- Top 5
- 범죄 유형 구성비
- 특별수사본부 출범 전후 12개월 비교
- 선택 기간 CSV 다운로드
- 선택 기간 JSON 다운로드(스키마·기간·필드 메타데이터 + 월별 원자료)
- 데이터 범위·최신 월·개월 수 자동 표시
- 검증된 새 CSV로 `data.js`를 갱신하면 기간 프리셋과 화면 범위 자동 확장
- 시스템 설정·저장된 선택을 반영하는 라이트/다크 모드
- 필터 상태 URL 저장·복원과 초기화
- 미관측 달을 `자료 없음`으로 구분
- 키보드 차트 탐색과 모바일 내부 스크롤
- 데이터 로드 실패 안내

기간의 시작과 종료를 역순으로 선택하면 실제 표시와 URL을 오름차순으로 정규화합니다. 2018년 범죄 유형은 원자료 불일치 때문에 세부 구성 대신 해당 연도의 합계와 안내 문구를 표시합니다.

## 자동 테스트

프로젝트 루트에서 실행합니다.

```bash
node --test
```

Node 테스트는 계산·URL·CSV·오류 처리와 `dashboard/`·`docs/` 실행 자산의 동일성을 확인합니다. Python 검증까지 포함하려면 다음 명령을 함께 실행합니다.

```bash
python -m unittest discover -s tests -p "test_*.py"
python analysis.py --validate-only
```

## 제출용 시나리오

1. 전체 기간 + 전체 단속인원
2. 2023~2025 + 전체 단속인원
3. 2020~2022 + 향정신성의약품
4. 특별수사본부 출범 전후 비교에서 전체·향정·마약·대마 전환

## GitHub Pages 배포

프로젝트의 `docs/` 폴더는 Dashboard와 동일한 배포용 복사본입니다.

1. 저장소에 프로젝트를 push합니다.
2. GitHub 저장소 → `Settings` → `Pages`
3. `Build and deployment` → **Deploy from a branch**
4. Branch: `main`
5. Folder: `/docs`
6. Save
7. 생성된 Pages URL을 프로젝트 README의 Dashboard URL에 입력합니다.

정적 사이트이므로 별도의 API Key 결제가 필요하지 않습니다.

현재 저장소는 https://github.com/lsh97nd-code/drug-trend-analysis 이며, GitHub Pages는 아직 설정되지 않았습니다.

## 데이터 갱신 및 2026~2027년 자료 추가

Dashboard의 범위 문구, 총 개월 수, 시작·종료 월, `전체`·`이후` 프리셋은 `data.js`의 실제 마지막 월을 기준으로 계산합니다. 새 공식 자료를 반영할 때는 `data.js`를 수작업하지 않고 갱신 도구를 사용합니다.

```bash
python update_dashboard_data.py --monthly data/processed/monthly_drug_offenders_2017_2027.csv --offense data/processed/yearly_offense_type_2017_2027.csv
```

도구는 다음을 검증한 후 `dashboard/data.js`와 `docs/data.js`를 동일하게 갱신합니다.

- 2017-01부터 마지막 연도 12월까지 누락·중복 없는 월 순서
- 모든 수치의 정수·비음수 조건과 마약류 종류별 합계
- 월별 연간 합계와 범죄 유형 연간 누계, 연도 범위
- 2018년 세부 결측과 2019년 2명 차이를 기존 검증 규칙대로 유지

검증 실패 시 출력을 바꾸지 않고, 두 파일 교체 중 문제가 발생하면 기존 버전을 복원합니다. 일치 여부만 검사하려면:

```bash
python update_dashboard_data.py --check
```

2026~2027년 값은 공식 월별·연간 CSV가 완전히 확보된 뒤에만 반영합니다. 미발표 월, 미래 값, 빈 세부 구성을 추정하여 채우지 않습니다.

갱신 후에는 표시 기간·개월 수·프리셋·차트·KPI·CSV/JSON 범위가 새 마지막 월에 맞게 자동 확장됩니다.

## JSON 다운로드 형식

JSON은 선택 기간의 7개 열 월별 데이터와 재사용을 위한 메타데이터를 저장합니다.

```json
{
  "schemaVersion": 1,
  "source": "대검찰청 월별 통계 기반 가공 데이터",
  "period": { "start": "2025-01", "end": "2025-12" },
  "rowCount": 12,
  "fields": ["date", "year", "month", "total", "cannabis", "narcotics", "psychotropics"],
  "data": []
}
```

CSV는 Spreadsheet 분석에, JSON은 JavaScript/Python 재사용이나 다른 Dashboard와의 데이터 교환에 적합합니다.
