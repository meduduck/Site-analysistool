import streamlit as st
import requests

st.set_page_config(page_title="대지분석 통합 엔진", page_icon="⚖️", layout="centered")

st.title("⚖️ 대지분석 통합 엔진: 현황 및 법규")
st.markdown("PNU 추출은 성공했습니다! 이제 **현황**과 **법규** 데이터를 강제로 불러옵니다.")

address_input = st.text_input("🔍 분석 대상지 주소", value="서울 중구 정동길 33")
kakao_key = st.text_input("🔑 카카오 REST API 키", type="password")

# 🚨 필립 님의 공공데이터 인증키 (가장 깨끗한 상태로 입력)
# 만약 아래 키로 안되면, 포털에서 'Encoding'된 키를 복사해서 넣어보세요.
SERVICE_KEY = "87443571551d327893c30af0d677644f98b96ca2e1186b65f6546848a1efb7f8"

if st.button("통합 데이터 분석 시작 🚀"):
    if not kakao_key:
        st.warning("카카오 키를 입력해 주세요.")
    else:
        # 1. 카카오 API: PNU 추출 (이미 검증됨)
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
            
            st.success(f"✅ 대상지 PNU 확인: {pnu}")

            # 2. 건축물대장 (404 에러 방지용 커스텀 URL)
            st.write("---")
            st.subheader("🏢 1. 건축물 현황 (건축물대장)")
            
            bld_url = "http://apis.data.go.kr/1613000/BldRgstHubService/getBrTitInfo"
            # 인증키 인코딩 문제를 피하기 위해 params 대신 직접 URL을 조립합니다.
            bld_full_url = f"{bld_url}?serviceKey={SERVICE_KEY}&sigunguCd={b_code[:5]}&bjdongCd={b_code[5:10]}&platGbCd={'0' if mnt=='1' else '1'}&bun={main_no}&ji={sub_no}&_type=json"
            
            try:
                res_bld = requests.get(bld_full_url, timeout=15)
                if res_bld.status_code == 200:
                    bld_data = res_bld.json()
                    items = bld_data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
                    if items:
                        info = items[0] if isinstance(items, list) else items
                        c1, c2 = st.columns(2)
                        c1.metric("주용도", info.get('mainPurpsCdNm', '정보없음'))
                        c2.metric("주구조", info.get('strctCdNm', '정보없음'))
                        st.write(f"**규모:** 지상 {info.get('grndFlrCnt', 0)}층 / 지하 {info.get('ugrndFlrCnt', 0)}층")
                    else:
                        st.info("건축물대장 정보가 없습니다.")
                else:
                    st.error(f"건축물대장 서버 응답 오류: {res_bld.status_code}")
            except: st.error("건축물대장 연결 실패")

            # 3. 토지이용계획 (500 에러 방지용)
            st.write("---")
            st.subheader("⚖️ 2. 토지 이용 및 법규 규제")
            
            land_url = "http://apis.data.go.kr/1613000/LndUtilInfoService/getLandUseAttr"
            land_full_url = f"{land_url}?serviceKey={SERVICE_KEY}&pnu={pnu}&_type=json"
            
            try:
                res_land = requests.get(land_full_url, timeout=15)
                if res_land.status_code == 200:
                    land_data = res_land.json().get('response', {}).get('body', {}).get('items', {}).get('item', [])
                    if land_data:
                        if isinstance(land_data, dict): land_data = [land_data]
                        rules = list(set([item.get('lndUseCharNm') for item in land_data if item.get('lndUseCharNm')]))
                        st.warning("⚠️ **주요 토지이용 규제사항**")
                        for rule in rules:
                            st.write(f"• {rule}")
                    else:
                        st.info("조회된 법규 사항이 없습니다.")
                else:
                    st.error(f"토지이용 API 응답 오류: {res_land.status_code}")
            except: st.error("법규 분석 서버 연결 실패")
