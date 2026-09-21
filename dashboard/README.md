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
- 달력 월별 평균
- Top 5
- 범죄 유형 구성비

## 제출용 시나리오

1. 전체 기간 + 전체 단속인원
2. 2023~2025 + 전체 단속인원
3. 2020~2022 + 향정신성의약품

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
