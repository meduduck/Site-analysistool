import streamlit as st
import requests
from requests.utils import unquote

st.set_page_config(page_title="대지분석 엔진 Pro", page_icon="⚖️", layout="centered")

st.title("⚖️ 대지분석 통합 엔진: 현황 및 법규")
st.markdown("주소 하나로 **PNU 추출 ➡️ 건축물대장 ➡️ 토지이용계획**을 한 번에 분석합니다.")

address_input = st.text_input("🔍 분석 대상지 주소", value="서울 중구 정동길 33")
kakao_key = st.text_input("🔑 카카오 REST API 키", type="password")

# 공공데이터 인증키 (필립 님 키)
# 🚨 중요: requests가 키를 이중 인코딩하지 않도록 unquote 처리합니다.
raw_key = "87443571551d327893c30af0d677644f98b96ca2e1186b65f6546848a1efb7f8"
DATA_GO_KEY = unquote(raw_key)

if st.button("통합 데이터 분석 시작 🚀"):
    if not kakao_key:
        st.warning("카카오 키를 입력해 주세요.")
    else:
        # 1. 카카오 API: PNU 추출
        kakao_url = "https://dapi.kakao.com/v2/local/search/address.json"
        headers = {"Authorization": f"KakaoAK {kakao_key}"}
        res_kakao = requests.get(kakao_url, headers=headers, params={"query": address_input})
        
        if res_kakao.status_code == 200 and res_kakao.json().get('documents'):
            doc = res_kakao.json()['documents'][0]
            addr = doc.get('address', {})
            b_code = addr.get('b_code', '')
            mnt = '2' if addr.get('mountain_yn') == 'Y' else '1'
            main_no = str(addr.get('main_address_no', '')).zfill(4)
            sub_no = str(addr.get('sub_address_no', '')).zfill(4)
            pnu = f"{b_code}{mnt}{main_no}{sub_no}"
            
            st.success(f"✅ 대상지 PNU: {pnu}")
            st.write("---")

            # 2. 건축물대장 API (현황)
            st.subheader("🏢 1. 건축물 현황 (건축물대장)")
            # 404 방지를 위해 http와 직접 URL 구성을 사용합니다.
            bld_url = "http://apis.data.go.kr/1613000/BldRgstHubService/getBrTitInfo"
            bld_params = {
                "serviceKey": DATA_GO_KEY,
                "sigunguCd": b_code[:5],
                "bjdongCd": b_code[5:10],
                "platGbCd": '0' if mnt=='1' else '1',
                "bun": main_no,
                "ji": sub_no,
                "_type": "json"
            }
            
            try:
                res_bld = requests.get(bld_url, params=bld_params, timeout=15)
                if res_bld.status_code == 200:
                    bld_items = res_bld.json().get('response', {}).get('body', {}).get('items', {}).get('item', [])
                    if bld_items:
                        info = bld_items[0] if isinstance(bld_items, list) else bld_items
                        c1, c2 = st.columns(2)
                        c1.metric("주용도", info.get('mainPurpsCdNm', '정보없음'))
                        c2.metric("주구조", info.get('strctCdNm', '정보없음'))
                        st.write(f"**규모:** 지상 {info.get('grndFlrCnt', 0)}층 / 지하 {info.get('ugrndFlrCnt', 0)}층")
                        st.write(f"**면적:** 대지 {info.get('platArea', 0)}㎡ / 연면적 {info.get('totArea', 0)}㎡")
                    else:
                        st.info("건축물대장 정보가 없는 나대지이거나 문화재 건축물일 수 있습니다.")
                else:
                    st.error(f"건축물대장 서버 응답 오류: {res_bld.status_code}")
            except:
                st.error("건축물대장 서버 연결 실패")

            # 3. 토지이용계획 API (법규)
            st.write("---")
            st.subheader("⚖️ 2. 토지 이용 및 법규 규제")
            
            # 토지이용계획정보 서비스 (속성조회)
            land_url = "http://apis.data.go.kr/1613000/LndUtilInfoService/getLandUseAttr"
            land_params = {
                "serviceKey": DATA_GO_KEY,
                "pnu": pnu,
                "numOfRows": "30",
                "pageNo": "1",
                "_type": "json"
            }
            
            try:
                res_land = requests.get(land_url, params=land_params, timeout=15)
                if res_land.status_code == 200:
                    land_data = res_land.json().get('response', {}).get('body', {}).get('items', {}).get('item', [])
                    if land_data:
                        if isinstance(land_data, dict): land_data = [land_data]
                        rules = list(set([item.get('lndUseCharNm') for item in land_data if item.get('lndUseCharNm')]))
                        
                        st.warning("⚠️ **주요 토지이용 규제사항**")
                        for rule in rules:
                            st.write(f"• {rule}")
                        
                        # 건축가 필터링 (중요 키워드 강조)
                        critical = [r for r in rules if any(k in r for k in ["상업", "주거", "문화재", "구역", "지구"])]
                        if critical:
                            st.info(f"💡 **설계 시 핵심 참고:** {', '.join(critical)}")
                    else:
                        st.info("조회된 법규 제한 사항이 없습니다.")
                else:
                    st.error(f"토지이용 API 응답 오류: {res_land.status_code}")
            except:
                st.error("법규 분석 서버 연결 실패")
                    
        else:
            st.error("주소 분석 실패. 정확한 지번 주소를 입력해 주세요.")
