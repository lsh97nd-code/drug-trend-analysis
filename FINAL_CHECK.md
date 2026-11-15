# 최종 구성 확인

## README.md 역할

README는 **프로젝트 사용설명서·안내문** 역할로 정리했다.

- 프로젝트 개요와 핵심 결과 요약
- 폴더 구조
- 설치 및 실행 방법
- 데이터 정제·검증 기준 요약
- 생성되는 시각화 목록
- 보너스 시계열 분해와 Dashboard 실행·배포 방법
- AI 사용 투명성 요약
- 제출 체크리스트
- 실제 GitHub 저장소 URL과 Pages 설정 상태
- 과제 안내 원본 7쪽과 제출 부록 3쪽을 합친 PDF 링크

상세한 그래프 해석과 원인 가설 검증은 REPORT로 넘겼다.

## REPORT.md 역할

REPORT는 **실제 조사·분석 보고서** 역할로 정리했다.

- 주제 선정 배경
- 분석 질문
- 데이터 설명
- 정제·검증 과정
- 시계열 분석 방법
- 기본 그래프 7개와 상세 해석
- Fact–Why–Action 인사이트 6개
- 외부 공식자료를 이용한 가설 검증
- 보너스 시계열 분해
- 보너스 Dashboard 구현·필터 시나리오
- 결론과 한계점
- AI 사용 로그

## Dashboard

- 정적 HTML/CSS/JavaScript 방식
- API Key 불필요
- 서버/DB 불필요
- `dashboard/` 로컬 실행용
- `docs/` GitHub Pages 배포용
- 필터: 기간, 시작·종료 월, 마약류 종류, 12개월 이동평균
- KPI, 월별 평균, Top 5, 범죄 유형 구성 제공
- 선택 기간의 각 월을 12개월 전과 비교하는 전년 동월 대비(YoY) 차트
- 특수본 출범 전후 12개월 비교와 7·8월 제외 민감도
- 선택 기간 CSV·JSON 다운로드와 URL 상태 복원
- 데이터 기간·개월 수·프리셋 자동 갱신 및 라이트/다크 모드
- 검증된 공식 CSV로 두 `data.js`를 함께 갱신하는 `update_dashboard_data.py`
- 키보드 탐색, 모바일 내부 스크롤, 데이터 로드 실패 안내

## 재현성 검증

- 월별 데이터 108행
- 중복 0
- 핵심 결측 0
- 대마+마약+향정=전체 불일치 0
- 기본 그래프 7개 + 시계열 분해 그래프 4개 생성
- Dashboard 데이터 108개월 로드 확인
- `analysis.py --validate-only`가 결과 파일을 변경하지 않고 통과
- Python·Node 전체 회귀 테스트와 `update_dashboard_data.py --check` 통과
- 2026~2027 합성 픽스처 확장 및 잘못된 입력에서 기존 출력 보존 확인
- Chrome에서 로컬 파일과 HTTP 실행, CSV·JSON 다운로드, 테마, YoY, 키보드, 모바일, 오류 화면 확인
- `dashboard/`와 `docs/` 실행 자산 동일성 확인

## 제출·배포 상태

- GitHub 저장소: https://github.com/lsh97nd-code/drug-trend-analysis
- 제출 PDF: `output/pdf/AI_데이터_분석_과제_제출본.pdf`
- GitHub Pages: 아직 설정되지 않음. `main /docs`를 배포 소스로 지정한 뒤 URL 기록 필요
