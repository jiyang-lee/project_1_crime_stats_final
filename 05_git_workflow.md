# Git 작업 순서 정리 (이 프로젝트 기준)

아래는 이 프로젝트를 여기까지 가져오는 동안 실제로 사용한 Git 작업 흐름을 **순서대로** 정리한 문서입니다.  
각 단계에 필요한 명령어를 모두 적었습니다.

---

## 1) 상태 확인
```bash
git status -sb
git branch --show-current
git log -1 --oneline
```

---

## 2) 변경 파일 추가/커밋
```bash
git add -A
git add path/to/file
git commit -m "your message"
```

---

## 3) 원격과 동기화 (충돌 방지)
```bash
git pull --rebase origin main
```

충돌이 생기면:
```bash
git status
# 충돌 해결 후
git add path/to/file
git rebase --continue
```

---

## 4) 푸시
```bash
git push origin main
```

---

## 5) 임시 변경 보관/복원 (stash)
```bash
git stash push -u -m "wip"
git stash pop
```

---

## 6) 파일/폴더 이름 변경
```bash
git mv old_name new_name
git status
git commit -m "chore: rename files"
```

---

## 7) 삭제 (안전하게)
```bash
git rm path/to/file
git commit -m "chore: remove file"
```

---

## 8) 원격/브랜치 확인
```bash
git remote -v
git branch -a
```

---

## 9) 특정 파일 추적 제외 (.gitignore)
```bash
# .gitignore 수정 후
git add .gitignore
git commit -m "chore: update gitignore"
```

---

## 10) 워크플로/자동화 관련
```bash
git add .github/workflows/hotspot-sync.yml
git commit -m "chore: update workflow"
git push origin main
```

---

## 11) 원격에 새 커밋이 생겼을 때 안전한 순서
```bash
git status -sb
git stash push -u -m "wip"
git pull --rebase origin main
git stash pop
git add -A
git commit -m "your message"
git push origin main
```

---

## 12) 확인용 자주 쓰는 명령어
```bash
git diff
git diff --staged
git show --stat -1
```
