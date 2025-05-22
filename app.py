import streamlit as st
import pandas as pd
import psycopg2
import json
import os
from dotenv import load_dotenv
from streamlit_autorefresh import st_autorefresh

# 환경변수에서 DB URL 불러오기
load_dotenv()
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

# DB 연결 및 데이터 로딩
def load_data():
    conn = psycopg2.connect(
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME
    )
    cur = conn.cursor()
    cur.execute("SELECT raw FROM bids_live ORDER BY raw->> 'bidNtceDate' DESC, raw->> 'bidNtceBgn' DESC")
    rows = cur.fetchall()
    conn.close()

    # raw JSONB → pandas DataFrame 변환
    raw_data = [(row[0]) for row in rows]
    df = pd.json_normalize(raw_data)
    return df

# Streamlit 앱 설정
st.set_page_config(page_title="입찰 공고 실시간 조회", layout="wide")
st.title("📢 나라장터 실시간 입찰 공고")

st_autorefresh(interval=300*1000, key='refresh')

try:
    # 먼저 환경변수가 제대로 설정되었는지 확인
    if not all([HOST, PORT, USER, PASSWORD, DBNAME]):
        st.error("❌ DB 연결 정보가 불완전합니다. .env 파일을 확인해주세요.")
    else:
        df = load_data()
        st.success(f"총 {len(df)}건의 공고를 불러왔습니다.")

    # 주요 컬럼만 표시
    df_display = df[[
        "bidNtceNo", "bidNtceNm", "bsnsDivNm", "ntceInsttNm",
        "bidNtceBgn", "bidClseDate", "bidNtceUrl"
    ]].rename(columns={
        "bidNtceNo": "입찰공고번호",
        "bidNtceNm": "입찰공고명",
        "bsnsDivNm": "업무구분명",
        "ntceInsttNm": "공고기관명",  # 여기에 콤마가 누락되었습니다
        "bidNtceBgn": "입찰공고일자",
        "bidClseDate": "입찰마감일자",
        "bidNtceUrl": "입찰공고URL"
    })

    # 검색 필터
    keyword = st.text_input("🔍 공고명/기관명 검색")
    if keyword:
        df_display = df_display[
            df_display["입찰공고명"].str.contains(keyword, case=False, na=False) |
            df_display["공고기관명"].str.contains(keyword, case=False, na=False)
            ]

        # 기본 데이터프레임 표시 대신 커스텀 테이블 형식으로 표시
        
    # 페이지네이션 구현 (임시)
    items_per_page = 10
    total_pages = len(df_display) // items_per_page + (1 if len(df_display) % items_per_page > 0 else 0)
        
    if total_pages > 0:
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            current_page = st.selectbox("페이지", options=list(range(1, total_pages + 1)), index=0)
            
        start_idx = (current_page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, len(df_display))
            
        # 현재 페이지의 데이터
        paginated_df = df_display.iloc[start_idx:end_idx].copy()
            
        # 테이블 헤더
        header_cols = st.columns([2, 1.5, 5, 3, 1.5, 1.5])
        headers = ['공고번호', '업무구분명', '입찰공고명', '공고기관명', '입찰공고일자', '입찰마감일자']
            
        for col, head in zip(header_cols, headers):
            col.markdown(f"**{head}**")
            
        st.markdown("<hr style='margin-top: 5px; margin-bottom: 10px;'>", unsafe_allow_html=True)  # 헤더 아래 구분선
            
        # 행 렌더링
        for _, row in paginated_df.iterrows():
            cols = st.columns([2, 1.5, 5, 3, 1.5, 1.5])
            cols[0].write(row["입찰공고번호"])
            cols[1].write(row["업무구분명"])
            
            # 공고명에 URL 링크 추가
            bid_title_link = f"[{row['입찰공고명']}]({row['입찰공고URL']})"
            cols[2].markdown(bid_title_link)
            
            cols[3].write(row["공고기관명"])
            cols[4].write(row["입찰공고일자"])
            cols[5].write(row["입찰마감일자"])
            
        # 페이지 네비게이션 (이전/다음)
        prev_page, _, next_page = st.columns([1, 3, 1])
            
        with prev_page:
            if current_page > 1:
                if st.button("◀ 이전"):
                    current_page -= 1
        
        with next_page:
            if current_page < total_pages:
                if st.button("다음 ▶"):
                    current_page += 1
    else:
        st.warning("검색 결과가 없습니다.")

except Exception as e:
    st.error(f"❌ 데이터 로딩 실패: {e}")
