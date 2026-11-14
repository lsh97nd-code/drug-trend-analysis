# VS Code → GitHub 업로드 및 GitHub Pages 배포 순서

## 1. 저장소 이름

Repository 이름: `drug-trend-analysis`

현재 저장소: https://github.com/lsh97nd-code/drug-trend-analysis

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

## 3. 현재 변경 검증

현재 저장소는 이미 초기화되어 있으므로 변경 파일과 테스트를 확인합니다.

```powershell
git status --short
python -m unittest discover -s tests -p "test_*.py"
node --test
```

검증 후 커밋합니다.

```powershell
git add --all
git commit -m "Improve validation dashboard and project documentation"
git push origin main
```

## 4. GitHub Repository 확인

push 후 https://github.com/lsh97nd-code/drug-trend-analysis 에서 커밋과 파일을 확인합니다.

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
https://lsh97nd-code.github.io/drug-trend-analysis/
```

배포 반영에는 몇 분 정도 걸릴 수 있습니다.

## 6. README.md에 실제 URL 입력

README.md에는 실제 저장소 주소가 기록되어 있습니다. Pages 설정이 완료되면 Dashboard URL만 갱신합니다.

```markdown
- GitHub 저장소: https://github.com/lsh97nd-code/drug-trend-analysis
- Dashboard URL: https://lsh97nd-code.github.io/drug-trend-analysis/
```

현재 GitHub Pages API에서는 사이트가 설정되지 않은 상태로 확인되었습니다. Pages 설정과 배포 성공을 확인한 후 URL을 완료 처리합니다.

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

