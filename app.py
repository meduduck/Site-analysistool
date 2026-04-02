import streamlit as st
import requests
import xml.etree.ElementTree as ET

st.set_page_config(page_title="대지분석 엔진 Pro", page_icon="⚖️", layout="centered")

st.title("⚖️ 대지분석 통합 엔진: 정동 프로젝트 전용")
st.markdown("캡처해주신 **진짜 API 주소**로 엔진을 완전히 재조립했습니다.")

address_input = st.text_input("🔍 분석 대상지 주소", value="서울 중구 정동길 33")
kakao_key = st.text_input("🔑 카카오 REST API 키", type="password")

# 🚨 필립 님의 검증된 인증키
SERVICE_KEY = "87443571551d327893c30af0d677644f98b96ca2e1186b65f6546848a1efb7f8"

if st.button("통합 데이터 분석 시작 🚀"):
    if not kakao_key:
        st.warning("카카오 키를 입력해 주세요.")
    else:
        # 1. 카카오 PNU 추출 (성공 확인됨)
        k_url = "https://dapi.kakao.com/v2/local/search/address.json"
        k_res = requests.get(k_url, headers={"Authorization": f"KakaoAK {kakao_key}"}, params={"query": address_input})
        
        if k_res.status_code == 200 and k_res.json().get('documents'):
            doc = k_res.json()['documents'][0]['address']
            pnu = f"{doc['b_code']}{'2' if doc['mountain_yn']=='Y' else '1'}{str(doc['main_address_no']).zfill(4)}{str(doc['sub_address_no']).zfill(4)}"
            st.success(f"✅ 대상지 PNU 확인: {pnu}")
            st.write("---")

            # 2. 건축물대장 (캡처 1번 기반)
            st.subheader("🏢 1. 건축물 현황 (건축물대장)")
            b_url = "http://apis.data.go.kr/1613000/BldRgstHubService/getBrTitInfo"
            b_params = {
                "serviceKey": SERVICE_KEY, "sigunguCd": pnu[:5], "bjdongCd": pnu[5:10],
                "platGbCd": "0", "bun": pnu[11:15], "ji": pnu[15:19], "_type": "json"
            }
            try:
                res_bld = requests.get(bld_url, params=bld_params, timeout=10)
                if res_bld.status_code == 200:
                    items = res_bld.json().get('response', {}).get('body', {}).get('items', {}).get('item', [])
                    if items:
                        info = items[0] if isinstance(items, list) else items
                        c1, c2 = st.columns(2)
                        c1.metric("주용도", info.get('mainPurpsCdNm', '-'))
                        c2.metric("주구조", info.get('strctCdNm', '-'))
                        st.write(f"**규모:** 지상 {info.get('grndFlrCnt')}층 / 지하 {info.get('ugrndFlrCnt')}층")
                    else: st.info("건축물 현황 데이터가 없습니다.")
                else: st.error(f"건축 서버 응답 오류 ({res_bld.status_code})")
            except: st.error("건축 서버 연결 실패")

            # 3. 토지이용규제 (캡처 2번 기반 - 핵심 수정!)
            st.write("---")
            st.subheader("⚖️ 2. 토지 이용 및 법규 규제")
            # 💡 캡처본에 적힌 진짜 엔드포인트와 기능명을 사용합니다.
            l_url = "http://apis.data.go.kr/1613000/arLandUseInfoService/DTarLandUseInfo"
            l_params = { "serviceKey": SERVICE_KEY, "pnu": pnu }
            
            try:
                # 캡처본에 'XML'만 적혀있으므로 XML로 받아 처리합니다.
                res_land = requests.get(l_url, params=l_params, timeout=10)
                if res_land.status_code == 200:
                    # XML 파싱 시작
                    root = ET.fromstring(res_land.content)
                    # lndUseCharNm 태그를 모두 찾아 리스트로 만듭니다.
                    rules = [node.text for node in root.findall(".//lndUseCharNm") if node.text]
                    
                    if rules:
                        rules = list(set(rules)) # 중복 제거
                        st.warning("⚠️ **주요 토지이용 규제사항**")
                        for r in rules:
                            st.write(f"• {r}")
                        if any("문화재" in r for r in rules):
                            st.error("🚨 **정동 프로젝트 핵심:** 문화재보호법 규제가 감지되었습니다!")
                    else: st.info("조회된 법규 제한 사항이 없습니다.")
                else: st.error(f"법규 서버 응답 오류 ({res_land.status_code})")
            except Exception as e: st.error(f"법규 분석 중 오류 발생: {e}")
