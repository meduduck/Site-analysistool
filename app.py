# (app.py 중간의 requests.get 부분을 이렇게 수정해 보세요)
with st.spinner("국토부 서버 대답을 기다리는 중 (최대 20초)..."):
    try:
        # 타임아웃을 20초로 대폭 늘렸습니다.
        res_bld = requests.get(bld_url, params=params, timeout=20)
        # ... 이하 동일
import streamlit as st
import requests

st.set_page_config(page_title="대지분석 엔진 테스트", page_icon="🏢", layout="centered")

st.title("🏢 대통합 엔진: 주소 하나로 건물 정보까지!")
st.markdown("카카오 API로 **PNU**를 추출하고, 이를 공공데이터에 넘겨 **건축물대장**을 조회합니다.")

if 'run_test' not in st.session_state:
    st.session_state.run_test = False

address_input = st.text_input("🔍 대상지 주소 (예: 서울 중구 정동길 33)", value="서울 중구 정동길 33")
kakao_key = st.text_input("🔑 카카오 REST API 키", type="password")

# 건축물대장 API 키
BLD_API_KEY = "87443571551d327893c30af0d677644f98b96ca2e1186b65f6546848a1efb7f8"

if st.button("마법의 데이터 추출 시작 🚀"):
    st.session_state.run_test = True

if st.session_state.run_test:
    if not kakao_key:
        st.warning("카카오 REST API 키를 입력해 주세요!")
    else:
        st.write("---")
        st.subheader("1단계: 카카오 API (주소 ➡️ PNU 변환)")
        
        kakao_url = "https://dapi.kakao.com/v2/local/search/address.json"
        headers = {"Authorization": f"KakaoAK {kakao_key}"}
        
        try:
            res_kakao = requests.get(kakao_url, headers=headers, params={"query": address_input}, timeout=5)
            
            if res_kakao.status_code == 200 and res_kakao.json().get('documents'):
                doc = res_kakao.json()['documents'][0]
                address_info = doc.get('address', {})
                
                if address_info:
                    b_code = address_info.get('b_code', '')
                    mountain_yn = '2' if address_info.get('mountain_yn') == 'Y' else '1' 
                    plat_gb_cd = '0' if mountain_yn == '1' else '1' 
                    main_no = str(address_info.get('main_address_no', '')).zfill(4)
                    sub_no = str(address_info.get('sub_address_no', '')).zfill(4)
                    
                    pnu_code = f"{b_code}{mountain_yn}{main_no}{sub_no}"
                    st.success(f"✅ **생성된 PNU:** {pnu_code}")
                    
                    # 2단계 시작
                    st.subheader("2단계: 공공데이터 API (건축물대장 정보 조회)")
                    # URL을 https로 변경하고 타임아웃을 늘렸습니다.
                    bld_url = "https://apis.data.go.kr/1613000/BldRgstHubService/getBrTitInfo"
                    
                    params = {
                        "serviceKey": BLD_API_KEY,
                        "sigunguCd": b_code[:5],       
                        "bjdongCd": b_code[5:10],      
                        "platGbCd": plat_gb_cd,        
                        "bun": main_no,                
                        "ji": sub_no,                  
                        "numOfRows": "10",
                        "pageNo": "1",
                        "_type": "json"                
                    }
                    
                    with st.spinner("국토교통부 서버 대답을 기다리는 중 (최대 10초)..."):
                        try:
                            # timeout=10을 추가하여 서버가 느려도 기다려줍니다.
                            res_bld = requests.get(bld_url, params=params, timeout=10)
                            
                            if res_bld.status_code == 200:
                                bld_data = res_bld.json()
                                items = bld_data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
                                
                                if items:
                                    if isinstance(items, dict): items = [items]
                                    info = items[0]
                                    st.success("✅ **건축물대장 조회 성공!**")
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.info(f"🏗️ **주구조:** {info.get('strctCdNm', '정보없음')}\n"
                                                f"🏢 **주용도:** {info.get('mainPurpsCdNm', '정보없음')}")
                                    with col2:
                                        st.success(f"층수: 지하 {info.get('ugrndFlrCnt', 0)}층 / 지상 {info.get('grndFlrCnt', 0)}층\n"
                                                   f"면적: 대지 {info.get('platArea', 0)}㎡ / 연면적 {info.get('totArea', 0)}㎡")
                                else:
                                    st.warning("대장 정보가 없습니다. 지번을 확인하거나 서버 점검 중일 수 있습니다.")
                            else:
                                st.error(f"공공데이터 서버 응답 오류: {res_bld.status_code}")
                        except requests.exceptions.Timeout:
                            st.error("⌛ 국토부 서버가 너무 느려 응답 시간을 초과했습니다. 잠시 후 다시 시도해 주세요.")
                        except Exception as e:
                            st.error(f"데이터 조회 중 오류: {e}")
                else:
                    st.error("PNU를 생성할 수 없는 주소입니다.")
            else:
                st.error("주소 검색 실패. 카카오 설정을 확인하세요.")
        except Exception as e:
            st.error(f"카카오 통신 오류: {e}")
