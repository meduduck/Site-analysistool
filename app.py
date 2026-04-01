import streamlit as st
import requests

st.set_page_config(page_title="대지분석 엔진 테스트", page_icon="🏢", layout="centered")

st.title("🏢 대통합 엔진: 주소 하나로 건물 정보까지!")
st.markdown("카카오 API로 **PNU**를 추출하고, 이를 공공데이터에 넘겨 **건축물대장**을 조회합니다.")

if 'run_test' not in st.session_state:
    st.session_state.run_test = False

address_input = st.text_input("🔍 대상지 주소 (예: 서울 중구 정동길 33)", value="서울 중구 정동길 33")
kakao_key = st.text_input("🔑 카카오 REST API 키", type="password")

# 발급받으신 건축물대장 API 키
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
        
        with st.spinner("카카오에서 주소를 분석 중입니다..."):
            res_kakao = requests.get(kakao_url, headers=headers, params={"query": address_input})
            
        # [디버깅용] 카카오 서버의 실제 대답 확인 박스
        with st.expander("🛠️ 시스템 응답 상세보기 (에러 추적용)"):
            st.write(f"상태 코드: {res_kakao.status_code}")
            st.json(res_kakao.json())
            
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
                bld_url = "http://apis.data.go.kr/1613000/BldRgstHubService/getBrTitInfo"
                
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
                
                with st.spinner("국토교통부 서버에서 건물을 조회 중입니다..."):
                    req_url = f"{bld_url}?serviceKey={BLD_API_KEY}&sigunguCd={params['sigunguCd']}&bjdongCd={params['bjdongCd']}&platGbCd={params['platGbCd']}&bun={params['bun']}&ji={params['ji']}&_type=json"
                    res_bld = requests.get(req_url)
                
                if res_bld.status_code == 200:
                    try:
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
                            st.warning("건축물대장 정보가 없습니다.")
                    except:
                        st.error("데이터 분석 중 오류가 발생했습니다.")
                else:
                    st.error(f"건축 API 연결 실패: {res_bld.status_code}")
            else:
                st.error("PNU를 생성할 수 없는 주소입니다.")
        else:
            st.error("카카오 주소 검색 실패. 아래 '시스템 응답 상세보기'를 확인해 보세요.")
