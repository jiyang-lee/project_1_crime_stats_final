# 1조 첫번째 프로젝트
## 프로젝트 명: 범죄 통계 알림e

## 실행 방법
- Streamlit 실행 파일: `4_streamlit/main.py`

```bash
streamlit run 4_streamlit/main.py
```

## 저장소 관리 원칙
- `4_streamlit` 폴더는 실행에 필요한 구조(`main.py`, `pages`, `orm`, `seed`, `data`, `static`)만 추적합니다.
- 로컬 산출물/임시 파일(`4_streamlit/crime_db.db`, `4_streamlit/2_sub.py`)은 `.gitignore`로 제외합니다.
