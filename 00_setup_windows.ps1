param(
    [switch]$Dev
)

$ErrorActionPreference = "Stop"

Write-Host "== project_1_crime_stats_final setup ==" -ForegroundColor Cyan

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "python을 찾을 수 없습니다. Python 3.11+ 설치 후 다시 실행하세요." -ForegroundColor Yellow
    Write-Host "설치 후 새 터미널을 열고 다음을 확인하세요: python --version" -ForegroundColor Yellow
    exit 1
}

python --version

if (-not (Test-Path ".venv")) {
    Write-Host "가상환경 생성: .venv" -ForegroundColor Cyan
    python -m venv .venv
}

Write-Host "가상환경 활성화" -ForegroundColor Cyan
try {
    . .\.venv\Scripts\Activate.ps1
} catch {
    Write-Host "Activate.ps1 실행이 막히면 아래를 먼저 실행하세요:" -ForegroundColor Yellow
    Write-Host "  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass" -ForegroundColor Yellow
    throw
}

Write-Host "pip 업그레이드 + requirements 설치" -ForegroundColor Cyan
python -m pip install --upgrade pip
pip install -r requirements.txt

if ($Dev) {
    Write-Host "dev requirements 설치(90_requirements_dev.txt)" -ForegroundColor Cyan
    pip install -r 90_requirements_dev.txt
}

Write-Host "완료. 실행 예시:" -ForegroundColor Green
Write-Host "  streamlit run main.py" -ForegroundColor Green

