# VS Code → GitHub 업로드 및 GitHub Pages 배포 순서

## 1. 저장소 이름

권장 Repository 이름: `drug-trend-analysis`

GitHub Pages를 무료로 사용하려면 GitHub Free 기준 저장소를 `Public`으로 생성합니다.

## 2. Git 사용자 정보 확인

VS Code에서 `터미널 → 새 터미널`을 열고 실행합니다.

```powershell
git config --global user.name
git config --global user.email
```

값이 비어 있으면 설정합니다.

```powershell
git config --global user.name "본인 이름 또는 Git 커밋에 표시할 이름"
git config --global user.email "GitHub 계정에서 확인 가능한 이메일"
```

> `user.name`은 Git 커밋 작성자 이름이며 GitHub 로그인 아이디와 반드시 같을 필요는 없습니다.

## 3. VS Code Source Control에서 Git 시작

1. VS Code 왼쪽 `소스 제어` 아이콘을 클릭합니다.
2. `Initialize Repository` 또는 `리포지토리 초기화`를 클릭합니다.
3. 변경 파일 전체를 확인합니다.
4. 첫 Commit message로 다음을 권장합니다.

```text
Initial commit: drug trend analysis project
```

5. `Commit`을 실행합니다.

## 4. GitHub Repository 생성 + 업로드

1. Source Control 상단의 `Publish to GitHub`를 클릭합니다.
2. GitHub 로그인 창이 뜨면 본인 계정으로 로그인합니다.
3. Repository 이름: `drug-trend-analysis`
4. Visibility: `Public`
5. 프로젝트 전체 파일을 선택하여 Publish합니다.

업로드 후 저장소 주소는 일반적으로 다음 형식입니다.

```text
https://github.com/<GitHub-username>/drug-trend-analysis
```

## 5. GitHub Pages 배포

GitHub 저장소 웹페이지에서:

1. `Settings`
2. 왼쪽 `Pages`
3. `Build and deployment`
4. Source: `Deploy from a branch`
5. Branch: `main`
6. Folder: `/docs`
7. `Save`

배포 URL은 일반적으로 다음 형식입니다.

```text
https://<GitHub-username>.github.io/drug-trend-analysis/
```

배포 반영에는 몇 분 정도 걸릴 수 있습니다.

## 6. README.md에 실제 URL 입력

README.md 마지막 `## 13. 프로젝트 URL`의 두 줄을 실제 주소로 바꿉니다.

```markdown
- GitHub 저장소: `https://github.com/<GitHub-username>/drug-trend-analysis`
- Dashboard URL: `https://<GitHub-username>.github.io/drug-trend-analysis/`
```

수정 후 두 번째 커밋을 권장합니다.

```text
Add GitHub Pages deployment URL
```

Commit 후 `Sync Changes` 또는 `Push`를 실행합니다.

## 7. 제출용 Dashboard 증빙 캡처

최소 다음 4장을 권장합니다.

1. Dashboard 전체 기간 + 전체 단속인원
2. 2023~2025 + 전체 단속인원
3. 2020~2022 + 향정신성의약품
4. GitHub Pages에서 실제 배포 URL이 보이는 화면

