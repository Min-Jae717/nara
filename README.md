# G2B 실시간 입찰공고 수집 & 시각화 시스템

이 프로젝트는 나라장터(G2B) 공공입찰공고를 실시간으로 수집하고,
Streamlit을 통해 사용자에게 시각화된 정보를 제공합니다.

## 주요 기능
- 실시간 공고 자동 수집 (5분 간격, GitHub Actions + SQLite)
- 공고/낙찰 목록 필터링 및 정렬
- GPT 요약 영역 (향후 확장 예정)

## 실행 방법

```bash
# 가상환경 설정 후
pip install -r requirements.txt
streamlit run app.py
