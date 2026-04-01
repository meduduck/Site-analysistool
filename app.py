import streamlit as st
import folium
from streamlit_folium import st_folium
import requests

st.set_page_config(page_title="대지분석 자동화 솔루션", page_icon="🏛️", layout="wide")
st.title("🏛️ 스마트 대지분석 대시보드 (v1.0)")

# 💡 [핵심 해결책] '세션 상태' 메모리 만들기
if 'run_analysis' not in st.session_state:
    st.session_state.run_analysis = False

with st.sidebar:
    st.header("📍 대상지 입력")
    # 정동길 좌표 기본값
    input_x = st.text_input("X 좌표 (경도)", value="126.972201078") 
    input_y = st.text_input("Y 좌표 (위도)", value="37.566244075")
    api_key = st.text_input("V-World API Key", type="password")
    
    # 버튼을 누르면 메모리를 True로 바꿉니다!
    if st.button("AI 대지 분석 시작 🚀"):
        st.session_state.run_analysis = True

# 이제 버튼 상태가 아니라 '메모리' 상태를 확인합니다.
if st.session_state.run_analysis:
    st.subheader("1. 대상지 위치 및 분석 바운더리")
    
    # 지도 띄우기
    m = folium.Map(location=[float(input_y), float(input_x)], zoom_start=17)
    folium.Marker([float(input_y), float(input_x)], popup="프로젝트 대상지").add_to(m)
    folium.Circle(radius=100, location=[float(input_y), float(input_x)], color="#3186cc", fill=True).add_to(m)
    
    # returned_objects=[] 를 추가하여 불필요한 새로고침을 한 번 더 막아줍니다.
    st_folium(m, width=800, height=400, returned_objects=[])

    st.subheader("2. 공공데이터 분석 결과")
    if api_key:
        # V-World API 통신 (용도지역 추출)
        url = "http://api.vworld.kr/req/data"
        params = {
            "service": "data", "request": "GetFeature", "data": "LT_C_UQ111",
            "key": api_key, "geomFilter": f"point({input_x} {input_y})",
            "geometry": "false", "format": "json"
        }
        try:
            res = requests.get(url, params=params, verify=False)
            if res.status_code == 200:
                features = res.json().get('response', {}).get('result', {}).get('featureCollection', {}).get('features', [])
                if features:
                    uname = features[0]['properties'].get('uname', '정보 없음')
                    st.success(f"📍 법적 용도지역: **{uname}**")
                else:
                    st.warning("❌ 해당 좌표에 용도지역 정보가 없습니다.")
        except Exception as e:
            st.error(f"🚨 통신 에러: {e}")
    else:
        st.info("👈 사이드바에 API 키를 입력하면 용도지역 데이터를 불러옵니다.")
