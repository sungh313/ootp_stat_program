# app.py

import streamlit as st
import subprocess
import sys

# --------------------------------------------------------------------------
# 각 페이지를 그리는 함수들
# --------------------------------------------------------------------------

def main_page():
    """메인 페이지 UI를 그립니다."""
    st.title("OOTP 분석 프로그램")
    st.write("")  # 공백 추가

    # '지금 저장된 데이터 확인하기' 버튼
    if st.button("지금 저장된 데이터 확인하기", use_container_width=True):
        st.session_state.page = 'view_data'  # 'page' 상태를 'view_data'로 변경
        st.rerun()  # 페이지를 즉시 새로고침

    # '새로운 데이터 저장하기' 버튼을 누르면 바로 Tkinter 앱 실행
    if st.button("새로운 데이터 저장하기", use_container_width=True):
        python_executable = sys.executable
        try:
            # Popen을 사용하여 별도의 프로세스로 uploader_gui.py 실행
            subprocess.Popen([python_executable, "uploader_gui.py"])
            # 사용자에게 업로더가 실행되었음을 알리는 작은 메시지 표시
            st.toast("데이터 업로더를 실행했습니다. 별도의 창을 확인해주세요.")
        except FileNotFoundError:
            st.error("uploader_gui.py 파일을 찾을 수 없습니다. app.py와 같은 폴더에 있는지 확인해주세요.")
        except Exception as e:
            st.error(f"업로더를 실행하는 중 오류가 발생했습니다: {e}")

def view_data_page():
    """'데이터 확인' 페이지 UI를 그립니다."""
    st.title("📊 지금 저장된 데이터 확인하기")
    st.write("이곳에 DB에서 불러온 선수 데이터를 표시할 예정입니다.")
    
    # 메인 페이지로 돌아가는 버튼
    if st.button("메인으로 돌아가기"):
        st.session_state.page = 'main'
        st.rerun()


# --------------------------------------------------------------------------
# 메인 로직: 현재 페이지 상태에 따라 적절한 페이지 함수를 호출
# --------------------------------------------------------------------------

# 'page' session_state가 없으면 'main'으로 초기화
if 'page' not in st.session_state:
    st.session_state.page = 'main'

# 현재 'page' 상태에 따라 해당 페이지 함수를 호출
if st.session_state.page == 'main':
    main_page()
elif st.session_state.page == 'view_data':
    view_data_page()

