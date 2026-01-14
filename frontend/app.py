import streamlit as st
import httpx
import json

API_BASE_URL = "http://localhost:8001/api/v1"

st.set_page_config(
    page_title="CryptoInsight Stock AI",
    layout="wide"
)

st.title("RAG 기반 주가 분석 AI")
st.markdown("---")

with st.sidebar:
    st.header("분석 설정")
    
    target_symbol = st.text_input(
        "분석할 종목 코드",
        value="AAPL",
        help="예: 애플(AAPL)"
    )
    
    st.markdown("---")
    st.header("데이터 파이프라인")
    
    if st.button("최신 뉴스 수집 (Finnhub)"):
        with st.spinner("Celery 워커에게 작업을 요청 중..."):
            try:
                response = httpx.post(f"{API_BASE_URL}/ingest/trigger/finnhub", timeout=5.0)
                if response.status_code == 200:
                    st.success(f"작업 시작됨: {response.json().get('task_id')}")
                else:
                    st.error(f"요청 실패: {response.status_code}")
            except Exception as e:
                st.error(f"서버 연결 오류: {e}")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("질문을 입력하세요 (예: 엔비디아 최근 실적과 주가 흐름 분석해줘)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        with st.spinner(f"'{target_symbol}' 주가 데이터와 뉴스를 분석 중입니다..."):
            try:
                payload = {
                    "query": prompt,
                    "symbol": target_symbol if target_symbol else None
                }
                
                response = httpx.post(
                    f"{API_BASE_URL}/chat/ask",
                    json=payload,
                    timeout=60.0 
                )
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "답변을 생성하지 못했습니다.")
                    references = data.get("references", [])

                    message_placeholder.markdown(answer)
                    
                    if references:
                        with st.expander("참고한 뉴스/문서 근거"):
                            for idx, ref in enumerate(references):
                                st.markdown(f"**{idx+1}. {ref['title']}**")
                                st.caption(ref['content'][:300] + "...")
                                st.markdown("---")
                    
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    
                else:
                    error_msg = f"서버 에러 ({response.status_code}): {response.text}"
                    message_placeholder.error(error_msg)
                    
            except httpx.ConnectError:
                message_placeholder.error("RAG 서버(Port 8001)에 연결할 수 없습니다.")
            except httpx.ReadTimeout:
                message_placeholder.error("답변 생성 시간이 초과되었습니다. (Timeout)")
            except Exception as e:
                message_placeholder.error(f"알 수 없는 오류 발생: {e}")