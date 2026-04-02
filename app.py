import streamlit as st
import requests

st.set_page_config(page_title="대지분석 엔진 Pro (V-World)", page_icon="🏢", layout="centered")

st.title("🏢 대지분석 통합 엔진: 브이월드 에디션")
st.markdown("브이월드 인증키를 적용하여 **용도지역 및 규제 사항**을 더 정확하게 분석합니다.")

address_input = st.text_input("🔍 분석 대상지 주소", value="서울 중구 정동길 33")
kakao_key = st.text_input("🔑 카카오 REST API 키", type="password")

# 🚨 발급받으신 브이월드 및 공공데이터 키
VWORLD_KEY = "D808BE8B-B942-326D-965B-353550D8B540"
DATA_GO_KEY = "87443571551d327893c30af0d677644f98b96ca2e1186b65f6546848a1efb7f8"

if st.button("통합 데이터 분석 시작 🚀"):
    if not kakao_key:
        st.warning("카카오 키를 먼저 입력해 주세요!")
    else:
        # 1. 카카오 API: PNU 추출
        k_url = "https://dapi.kakao.com/v2/local/search/address.json"
        k_res = requests.get(k_url, headers={"Authorization": f"KakaoAK {kakao_key}"}, params={"query": address_input})
        
        if k_res.status_code == 200 and k_res.json().get('documents'):
            doc = k_res.json()['documents'][0]['address']
            pnu = f"{doc['b_code']}{'2' if doc['mountain_yn']=='Y' else '1'}{str(doc['main_address_no']).zfill(4)}{str(doc['sub_address_no']).zfill(4)}"
            st.success(f"✅ 대상지 PNU 확인: {pnu}")
            st.write("---")

            # 2. 건축물대장 (공공데이터포털)
            st.subheader("🏢 1. 건축물 현황")
            b_url = "http://apis.data.go.kr/1613000/BldRgstHubService/getBrTitInfo"
            b_params = {
                "serviceKey": DATA_GO_KEY, "sigunguCd": pnu[:5], "bjdongCd": pnu[5:10],
                "platGbCd": "0", "bun": pnu[11:15], "ji": pnu[15:19], "_type": "json"
            }
            try:
                res_bld = requests.get(bld_url, params=b_params, timeout=10)
                items = res_bld.json().get('response', {}).get('body', {}).get('items', {}).get('item', [])
                if items:
                    info = items[0] if isinstance(items, list) else items
                    c1, c2 = st.columns(2)
                    c1.metric("주용도", info.get('mainPurpsCdNm', '-'))
                    c2.metric("주구조", info.get('strctCdNm', '-'))
                    st.caption(f"규모: 지상 {info.get('grndFlrCnt')}층 / 지하 {info.get('ugrndFlrCnt')}층")
                else: st.info("건축물대장 정보가 없습니다.")
            except: st.error("건축물대장 서버 연결 지연")

            # 3. 브이월드: 토지이용규제 (용도지역/지구)
            st.write("---")
            st.subheader("⚖️ 2. 토지 이용 및 법규 규제 (V-World)")
            
            # 브이월드 데이터 API 주소 (용도지역지구 레이어: LT_C_UQ111)
            v_url = "https://api.vworld.kr/req/data"
            v_params = {
                "key": VWORLD_KEY,
                "domain": "https://site-analysistool-apn4rqxmavifyhl7h2sk9f.streamlit.app",
                "service": "data",
                "version": "2.0",
                "request": "getfeature",
                "format": "json",
                "size": "100",
                "data": "LT_C_UQ111", # 용도지역지구 레이어
                "attrFilter": f"pnu:like:{pnu}"
            }
            
            with st.spinner("브이월드에서 법규 정보를 가져오는 중..."):
                try:
                    res_v = requests.get(v_url, params=v_params, timeout=10)
                    if res_v.status_code == 200:
                        v_data = res_v.json()
                        features = v_data.get('response', {}).get('result', {}).get('featureCollection', {}).get('features', [])
                        
                        if features:
                            # 법규 명칭(u_name)만 쏙쏙 뽑아 중복 제거
                            rules = list(set([f['properties'].get('u_name') for f in features if f['properties'].get('u_name')]))
                            
                            st.warning("⚠️ **주요 토지이용 규제사항**")
                            for r in rules:
                                st.write(f"• {r}")
                            
                            # 정동 프로젝트 맞춤형 강조
                            if any("상업" in r for r in rules):
                                st.info("💡 **분석 결과:** 본 대지는 **상업지역**에 속해있어 높은 개발 잠재력을 가지고 있습니다.")
                            if any("문화재" in r for r in rules):
                                st.error("🚨 **중요 법규:** 문화재 보호 관련 규제가 확인됩니다. 설계 시 심의가 필요할 수 있습니다.")
                        else:
                            st.info("조회된 용도지역 정보가 없습니다.")
                    else:
                        st.error(f"브이월드 응답 오류 ({res_v.status_code})")
                except Exception as e:
                    st.error(f"브이월드 통신 중 오류: {e}")
