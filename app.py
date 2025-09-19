# app.py (수정 완료된 전체 코드)

import streamlit as st
import subprocess
import sys
import webbrowser
import time
import signal
import os

# --------------------------------------------------------------------------
# 전역 변수 및 헬퍼 함수
# --------------------------------------------------------------------------

# 선수 분석 웹서버 프로세스를 저장할 변수
if 'analysis_process' not in st.session_state:
    st.session_state.analysis_process = None

def start_analysis_server():
    """선수 분석 웹서버(Flask 앱)를 실행하고, 브라우저를 엽니다."""
    
    # 이미 실행 중인 프로세스가 있다면 종료
    if st.session_state.analysis_process and st.session_state.analysis_process.poll() is None:
        try:
            os.kill(st.session_state.analysis_process.pid, signal.SIGTERM)
            st.session_state.analysis_process.wait()
            st.toast("기존 분석 서버를 종료했습니다.")
        except OSError as e:
            st.warning(f"기존 프로세스 종료 실패: {e}")

    try:
        # Flask 앱을 별도의 프로세스로 실행
        python_executable = sys.executable
        process = subprocess.Popen([python_executable, "player_info_app.py"])
        st.session_state.analysis_process = process
        st.toast("선수 분석 서버를 시작합니다... 잠시만 기다려주세요.")
        
        # 서버가 시작될 시간을 2초간 기다림
        time.sleep(2)
        
        # 웹 브라우저로 분석 화면 열기
        webbrowser.open_new_tab('http://127.0.0.1:5001')
        
    except FileNotFoundError:
        st.error("player_info_app.py 파일을 찾을 수 없습니다. app.py와 같은 폴더에 있는지 확인해주세요.")
    except Exception as e:
        st.error(f"선수 분석 프로그램을 실행하는 중 오류가 발생했습니다: {e}")

# --------------------------------------------------------------------------
# 메인 페이지 UI
# --------------------------------------------------------------------------

st.set_page_config(page_title="OOTP 분석 프로그램", layout="centered")

st.title("🦅 OOTP 분석 프로그램")
st.write("한화 이글스 데이터 분석을 위한 프로그램입니다.")
st.write("")  # 공백

# '지금 저장된 데이터 확인하기' 버튼
if st.button("📊 지금 저장된 데이터 확인하기", use_container_width=True, help="DB에 저장된 선수 정보를 웹 브라우저로 확인합니다."):
    start_analysis_server()

st.write("") # 버튼 사이 공백

# '새로운 데이터 저장하기' 버튼
if st.button("💾 새로운 데이터 저장하기", use_container_width=True, help="데이터 업로더를 실행하여 새로운 데이터를 DB에 저장합니다."):
    python_executable = sys.executable
    try:
        # Popen을 사용하여 별도의 프로세스로 uploader_gui.py 실행
        subprocess.Popen([python_executable, "uploader_gui.py"])
        st.toast("데이터 업로더를 실행했습니다. 별도의 창을 확인해주세요.")
    except FileNotFoundError:
        st.error("uploader_gui.py 파일을 찾을 수 없습니다. app.py와 같은 폴더에 있는지 확인해주세요.")
    except Exception as e:
        st.error(f"업로더를 실행하는 중 오류가 발생했습니다: {e}")

# Streamlit 앱이 종료될 때 자식 프로세스도 함께 종료되도록 설정
# (이 기능은 Streamlit의 세션 관리 방식으로 인해 완벽하게 작동하지 않을 수 있음)
# st.on_stop(kill_child_process) # 이 기능은 최신 Streamlit 버전에서 지원하지 않을 수 있음

