# Streamlit 비밀(Secrets) 설정 안내

이 문서는 로컬 개발 및 Streamlit 배포에서 API 키를 안전하게 관리하는 방법을 정리합니다.

- 로컬: `.env` 파일 사용 (저장소에 커밋하지 마세요).
- Streamlit (Cloud): 프로젝트 설정의 Secrets 환경에 키를 등록하세요.
- Streamlit (로컬 앱): `.streamlit/secrets.toml` 사용 가능합니다 (실제 파일은 커밋하지 마세요).

1) 로컬 실행 (Windows PowerShell 예)

```powershell
# 1) .env 파일 생성 (프로젝트 루트에 .env 추가)
# 내용 예: SEOUL_API_KEY=your_real_key_here
# 실행하기 전에는 .env가 .gitignore에 포함되어 있어야 합니다.

# 2) 가상환경 활성화 및 실행
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt  # 필요 시
python 4_streamlit/1_main.py     # 또는 Streamlit으로 실행
streamlit run 4_streamlit/1_main.py
```

2) `.streamlit/secrets.toml` 예시 (로컬 테스트용)

```toml
# 복사해서 .streamlit/secrets.toml 로 저장 (커밋 금지)
SEOUL_API_KEY = "your_real_key_here"
```

3) Streamlit Cloud 배포 시 (Secrets 설정)

- Streamlit Cloud 대시보드 → 앱 → Settings → Secrets 에 `SEOUL_API_KEY` 키를 추가하세요.
- 앱은 자동으로 `st.secrets["SEOUL_API_KEY"]` 또는 환경변수 `SEOUL_API_KEY`로 접근 가능합니다.

4) 코드 변경 요약

- `4_streamlit/seed/seoul_collector_30min.py`는 이제 우선적으로 환경변수 `SEOUL_API_KEY`를 확인하고, 없으면 `st.secrets`에서 읽습니다. 환경변수가 없으면 실행을 중단합니다.

5) 체크리스트

- [x] `.env.sample` 추가됨
- [x] `.streamlit/secrets.sample.toml` 추가됨
- [x] `seoul_collector_30min.py`가 환경/Streamlit secrets에서 키를 읽도록 변경됨
- [ ] README에 배포 절차 추가 (원하면 제가 추가해드릴게요)

필요하면 제가 README에 배포 섹션을 바로 추가하거나, 다른 파일들도 동일한 방식으로 리팩터링해드릴게요.