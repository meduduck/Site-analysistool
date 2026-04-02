import streamlit as st
import requests

# 1. 페이지 기본 설정 (아이패드 앱 인터페이스 최적화)
st.set_page_config(
    page_title="Site Analysis Pro", 
    page_icon="🏢", 
    layout="centered"
)

# 커스텀 CSS: 건축가용 세련된 디자인
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🏢 대지분석 통합 엔진 Pro")
st.caption("Architecture Site Analysis Tool for Philip Jang")

# 2. 사용자 입력 및 키 설정
with st.container():
    addr_input = st.text_input("🔍 분석 대상지 지번 주소", value="서울 중구 정동길 33")
    kakao_key = st.text_input("🔑 Kakao REST API Key", type="password")

# --- 설정값 (필립 님의 인증키들) ---
VWORLD_KEY = "D808BE8B-B942-326D-965B-353550D8B540"
PUBLIC_DATA_KEY = "87443571551d327893c30af0d677644f98b96ca2e1186b65f6546848a1efb7f8"
# 브이월드 설정과 동일하게 슬래시(/)를 포함한 도메인 주소
MY_DOMAIN = "https://site-analysistool-apn4rqxmavifyhl7h2sk9f.streamlit.app/"

if st.button("통합 데이터 분석 시작 🚀"):
    if not kakao_key:
        st.warning("카카오 API 키를 입력해 주세요.")
    else:
        # ---------------------------------------------------------
        # STEP 1. 카카오 API - 주소 → PNU 변환
        # ---------------------------------------------------------
        with st.spinner("카카오 지적 데이터 조회 중..."):
            k_url = "https://dapi.kakao.com/v2/local/search/address.json"
            k_res = requests.get(k_url, headers={"Authorization": f"KakaoAK {kakao_key}"}, params={"query": addr_input})
            
            if k_res.status_code == 200 and k_res.json().get('documents'):
                addr_data = k_res.json()['documents'][0]['address']
                b_code = addr_data['b_code']
                mnt_yn = '2' if addr_data['mountain_yn'] == 'Y' else '1'
                main_no = str(addr_data['main_address_no']).zfill(4)
                sub_no = str(addr_data['sub_address_no']).zfill(4)
                pnu = f"{b_code}{mnt_yn}{main_no}{sub_no}"
                
                st.success(f"📍 대상지 PNU 확인: {pnu}")
                st.write("---")

                # ---------------------------------------------------------
                # STEP 2. 국토부 API - 건축물대장 (현황 정보)
                # ---------------------------------------------------------
                st.subheader("🏢 1. 건축물 현황 (건축물대장)")
                # 인증키 인코딩 문제를 피하기 위해 직접 URL 조립
                b_base = "http://apis.data.go.kr/1613000/BldRgstHubService/getBrTitInfo"
                b_url = f"{b_base}?serviceKey={PUBLIC_DATA_KEY}&sigunguCd={b_code[:5]}&bjdongCd={b_code[5:10]}&platGbCd={'0' if mnt_yn=='1' else '1'}&bun={main_no}&ji={sub_no}&_type=json"
                
                try:
                    b_res = requests.get(b_url, timeout=15)
                    if b_res.status_code == 200:
                        b_items = b_res.json().get('response', {}).get('body', {}).get('items', {}).get('item', [])
                        if b_items:
                            info = b_items[0] if isinstance(b_items, list) else b_items
                            c1, c2, c3 = st.columns(3)
                            c1.metric("주용도", info.get('mainPurpsCdNm', '-'))
                            c2.metric("주구조", info.get('strctCdNm', '-'))
                            c3.metric("높이", f"{info.get('heit', 0)}m")
                            st.write(f"**규모:** 지상 {info.get('grndFlrCnt')}층 / 지하 {info.get('ugrndFlrCnt')}층")
                        else:
                            st.info("건축물 현황 정보가 없는 나대지입니다.")
                    else:
                        st.error(f"국토부 서버 응답 지연 (Code: {b_res.status_code})")
                except:
                    st.error("건축물대장 서버 연결 실패")

                # ---------------------------------------------------------
                # STEP 3. 브이월드 API - 토지이용규제 (법규 정보)
                # ---------------------------------------------------------
                st.write("---")
                st.subheader("⚖️ 2. 토지 이용 및 법규 규제 (V-World)")
                
                v_url = "https://api.vworld.kr/req/data"
                v_params = {
                    "key": VWORLD_KEY,
                    "domain": MY_DOMAIN,
                    "service": "data", "version": "2.0", "request": "getfeature",
                    "format": "json", "size": "100",
                    "data": "LT_C_UQ111", # 용도지역지구 레이어
                    "attrFilter": f"pnu:like:{pnu}"
                }
                
                with st.spinner("브이월드 법규 데이터 분석 중..."):
                    try:
                        v_res = requests.get(v_url, params=v_params, timeout=15)
                        if v_res.status_code == 200:
                            v_json = v_res.json()
                            features = v_json.get('response', {}).get('result', {}).get('featureCollection', {}).get('features', [])
                            
                            if features:
                                rules = list(set([f['properties'].get('u_name') for f in features if f['properties'].get('u_name')]))
                                st.warning("⚠️ **주요 토지이용 규제사항**")
                                for r in rules:
                                    st.write(f"• {r}")
                                
                                # 건축가 전용 분석 메시지
                                if any("문화재" in r for r in rules):
                                    st.error("🚨 **정동 프로젝트 핵심:** 문화재보호법에 따른 높이 및 외관 심의 대상입니다.")
                                if any("상업" in r for r in rules):
                                    st.info("💡 **용도지역:** 상업지역입니다. 건폐율/용적률 이득을 극대화할 수 있습니다.")
                            else:
                                st.info("조회된 법규 제한 사항이 없습니다.")
                        else:
                            st.error(f"브이월드 인증 오류 ({v_res.status_code}) - 도메인 설정을 확인하세요.")
                    except:
                        st.error("브이월드 서버 연결 실패")
            else:
                st.error("입력하신 주소를 찾을 수 없습니다. 정확한 지번 주소를 입력해 주세요.")

# 푸터
st.write("---")
st.caption(f"© 2026 Architect Philip Jang. Site analysis for Jeong-dong Shin-A Ilbo Project.")
