import streamlit as st
import requests

st.set_page_config(page_title="대지분석 엔진 테스트", page_icon="🏢", layout="centered")

st.title("🏢 대통합 엔진: 주소 하나로 건물 정보까지!")
st.markdown("카카오 API로 **PNU**를 추출하고, 이를 공공데이터에 넘겨 **건축물대장**을 조회합니다.")

# 상태 유지 메모리
if 'run_test' not in st.session_state:
    st.session_state.run_test = False

address_input = st.text_input("🔍 대상지 주소 (예: 서울 중구 정동길 33)", value="서울 중구 정동길 33")
kakao_key = st.text_input("🔑 카카오 REST API 키 (여기에 입력하세요)", type="password")

# 방금 발급받으신 건축물대장 API 키 (하드코딩)
BLD_API_KEY = "87443571551d327893c30af0d677644f98b96ca2e1186b65f6546848a1efb7f8"

if st.button("마법의 데이터 추출 시작 🚀"):
    st.session_state.run_test = True

if st.session_state.run_test:
    if not kakao_key:
        st.warning("카카오 REST API 키를 입력해 주세요!")
    else:
        st.write("---")
        # -----------------------------------------------------
        # 1단계: 카카오 API로 좌표 및 PNU 추출
        # -----------------------------------------------------
        st.subheader("1단계: 카카오 API (주소 ➡️ PNU 변환)")
        
        kakao_url = "https://dapi.kakao.com/v2/local/search/address.json"
        headers = {"Authorization": f"KakaoAK {kakao_key}"}
        
        with st.spinner("카카오에서 주소를 분석 중입니다..."):
            res_kakao = requests.get(kakao_url, headers=headers, params={"query": address_input})
                    with st.spinner("카카오에서 주소를 분석 중입니다..."):
            res_kakao = requests.get(kakao_url, headers=headers, params={"query": address_input})
        
        # 🚨 [추가] 카카오 서버의 실제 대답을 확인하는 디버깅용 박스
        with st.expander("🛠️ 시스템 응답 상세보기 (에러 추적용)"):
            st.write(f"상태 코드: {res_kakao.status_code}")
            st.json(res_kakao.json())

        if res_kakao.status_code == 200 and res_kakao.json()['documents']:
            doc = res_kakao.json()['documents'][0]
            address_info = doc.get('address', {})
            
            if address_info:
                # PNU 조립
                b_code = address_info.get('b_code', '')
                mountain_yn = '2' if address_info.get('mountain_yn') == 'Y' else '1' # 보통 대지는 1, 산은 2 (공공데이터 기준은 0/1이기도 함)
                plat_gb_cd = '0' if mountain_yn == '1' else '1' # 공공데이터용 대지구분코드 변환
                main_no = str(address_info.get('main_address_no', '')).zfill(4)
                sub_no = str(address_info.get('sub_address_no', '')).zfill(4)
                
                pnu_code = f"{b_code}{mountain_yn}{main_no}{sub_no}"
                
                st.success(f"✅ **생성된 PNU:** {pnu_code}")
                
                # -----------------------------------------------------
                # 2단계: 공공데이터 API로 건축물대장 조회
                # -----------------------------------------------------
                st.subheader("2단계: 공공데이터 API (건축물대장 정보 조회)")
                
                # 건축HUB API 기본개요/표제부 URL (버전 1.0 기준)
                bld_url = "http://apis.data.go.kr/1613000/BldRgstHubService/getBrTitInfo"
                
                # PNU를 각 항목으로 분리해서 파라미터로 전달
                params = {
                    "serviceKey": BLD_API_KEY,
                    "sigunguCd": b_code[:5],       # 시군구코드 (앞 5자리)
                    "bjdongCd": b_code[5:10],      # 법정동코드 (뒤 5자리)
                    "platGbCd": plat_gb_cd,        # 대지구분코드
                    "bun": main_no,                # 본번
                    "ji": sub_no,                  # 부번
                    "numOfRows": "10",
                    "pageNo": "1",
                    "_type": "json"                # JSON 형태로 결과 받기
                }
                
                with st.spinner("국토교통부 서버에서 건물을 조회 중입니다..."):
                    # 공공데이터 API는 키 인코딩 문제 때문에 수동으로 url 조합하는 것이 안전함
                    req_url = f"{bld_url}?serviceKey={BLD_API_KEY}&sigunguCd={params['sigunguCd']}&bjdongCd={params['bjdongCd']}&platGbCd={params['platGbCd']}&bun={params['bun']}&ji={params['ji']}&_type=json"
                    res_bld = requests.get(req_url)
                
                if res_bld.status_code == 200:
                    try:
                        bld_data = res_bld.json()
                        items = bld_data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
                        
                        if items:
                            # 아이템이 여러 개일 수 있으나 첫 번째 표제부만 확인
                            if isinstance(items, dict):
                                items = [items]
                            
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
                            st.warning("건축물대장 정보가 없습니다. (나대지이거나 지번이 다를 수 있습니다.)")
                    except Exception as e:
                        st.error(f"공공데이터 JSON 파싱 에러 (서버 점검 중일 수 있습니다): {e}")
                        with st.expander("원본 데이터 확인"):
                            st.write(res_bld.text)
                else:
                    st.error(f"건축물대장 API 연결 실패: {res_bld.status_code}")
                    
            else:
                st.error("정확한 지번 정보가 없어 PNU를 조합할 수 없습니다.")
        else:
            st.error("카카오 주소 검색 실패. 주소를 다시 확인해 주세요.")
