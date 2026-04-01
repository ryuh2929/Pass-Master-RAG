import streamlit as st
from src.main import get_rag_response, get_stats_response, is_statistical_query

# 웹 페이지 설정
st.set_page_config(page_title="정처기 합격 마스터", page_icon="🎓")
st.title("🎓 정보처리기사 합격 마스터 RAG")
st.caption("과거 기출 데이터를 분석하여 최적의 답안을 제시합니다.")

# 세션 상태 초기화 (대화 기록 저장용)
if "messages" not in st.session_state:
    st.session_state.messages = []

# 기존 대화 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자 입력 받기
if prompt := st.chat_input("질문을 입력하세요 (예: 결합도의 종류와 특징 알려줘)"):
    # 유저 메시지 표시 및 저장
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 챗봇 답변 생성
    with st.chat_message("assistant"):
        with st.spinner("기출 데이터를 분석 중입니다..."):
            # 통계 쿼리인지 RAG 쿼리인지 판별하여 로직 호출
            if is_statistical_query(prompt):
                response = get_stats_response(prompt)
            else:
                response = get_rag_response(prompt)
            
            st.markdown(response, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": response})