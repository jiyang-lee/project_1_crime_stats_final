# 관리자(Admin) 페이지 사용 방법

## 1) 무엇을 할 수 있나요?
- 핫스팟 데이터 `active` 값(활성/비활성) 변경
- 핫스팟(AREA_NM/area_name) ↔ 지역(RegionMaster) 매핑 저장/수정

## 2) 비밀번호 설정(필수)
관리자 페이지는 `ADMIN_PASSWORD`가 설정되어 있어야 접근할 수 있습니다.

### 옵션 A) Streamlit secrets 사용(권장)
`project_1_crime_stats_final/.streamlit/secrets.toml`에 아래를 추가합니다.

```toml
ADMIN_PASSWORD = "원하는-비밀번호"
```

### 옵션 B) 환경변수 사용
PowerShell 예시:

```powershell
$env:ADMIN_PASSWORD="원하는-비밀번호"
```

## 3) 앱 실행
레포 루트에서:

```bash
streamlit run main.py
```

## 4) 관리자 페이지 위치
사이드바 네비게이션에 **관리 → 관리자**가 추가됩니다.

