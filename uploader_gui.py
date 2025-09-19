# 파일명: uploader_gui.py (최종 버전)

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading
import os
import glob
import datetime
import traceback
import json # 경로 저장을 위해 json 모듈 추가

from db_handler import execute_sql_from_file

# --- 🚨 핵심 변경점 (1): 설정 파일 경로 정의 🚨 ---
# 사용자의 홈 디렉토리에 설정 파일을 저장하여 프로그램 위치와 관계없이 경로를 기억합니다.
CONFIG_FILE = os.path.join(os.path.expanduser('~'), '.ootp_uploader_config.json')

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("OOTP SQL Uploader")
        self.master.geometry("600x450")
        self.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.selected_root_folder = ""
        self.create_widgets()
        self.load_last_path() # 프로그램 시작 시 마지막 경로를 불러옵니다.

    def create_widgets(self):
        file_frame = tk.Frame(self)
        file_frame.pack(fill=tk.X, pady=5)
        
        self.file_label = tk.Label(file_frame, text="선택된 폴더:", width=10, anchor="w")
        self.file_label.pack(side=tk.LEFT, padx=(0, 5))

        self.path_var = tk.StringVar()
        self.path_var.set("상위 폴더를 선택해주세요.")
        self.path_entry = tk.Entry(file_frame, textvariable=self.path_var, state='readonly')
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.select_button = tk.Button(file_frame, text="폴더 선택", command=self.select_folder)
        self.select_button.pack(side=tk.LEFT, padx=(5, 0))

        self.upload_button = tk.Button(self, text="DB에 업로드", command=self.start_upload, height=2)
        self.upload_button.pack(fill=tk.X, pady=10)
        
        self.status_text = scrolledtext.ScrolledText(self, wrap=tk.WORD, state='disabled', height=15)
        self.status_text.pack(fill=tk.BOTH, expand=True)

    def load_last_path(self):
        """설정 파일에서 마지막으로 사용한 폴더 경로를 불러옵니다."""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    last_path = config.get('last_path')
                    if last_path and os.path.isdir(last_path):
                        self.selected_root_folder = last_path
                        self.path_var.set(last_path)
                        self.log_to_gui(f"저장된 경로를 불러왔습니다: {last_path}\n")
        except Exception as e:
            self.log_to_gui(f"경로 불러오기 실패: {e}\n")

    def save_last_path(self, path):
        """선택한 폴더 경로를 설정 파일에 저장합니다."""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump({'last_path': path}, f, indent=4)
        except Exception as e:
            self.log_to_gui(f"경로 저장 실패: {e}\n")

    def select_folder(self):
        folderpath = filedialog.askdirectory(title="OOTP 덤프가 저장된 상위 폴더를 선택하세요")
        if folderpath:
            self.selected_root_folder = folderpath
            self.path_var.set(folderpath)
            self.log_to_gui(f"상위 폴더 선택됨: {folderpath}\n")
            self.save_last_path(folderpath) # 새로운 경로를 저장합니다.

    def start_upload(self):
        if not self.selected_root_folder:
            messagebox.showwarning("경고", "먼저 상위 폴더를 선택해야 합니다.")
            return

        self.upload_button.config(state="disabled")
        self.select_button.config(state="disabled")
        self.clear_gui_log()
        
        upload_thread = threading.Thread(target=self.process_upload_logic, daemon=True)
        upload_thread.start()
        self.master.after(100, self.check_thread, upload_thread)

    def process_upload_logic(self):
        log_folder = os.path.join(self.selected_root_folder, 'logs')
        os.makedirs(log_folder, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_filename = os.path.join(log_folder, f"upload_log_{timestamp}.txt")
        
        # --- 🚨 핵심 변경점 (2): 성공/실패 카운터 추가 🚨 ---
        success_count = 0
        failure_count = 0
        skipped_count = 0

        try:
            # ... (폴더 탐색 로직은 동일)
            self.log_to_gui("="*50 + "\n")
            self.log_to_gui("하위의 최신 'dump' 폴더를 탐색합니다...\n")
            subfolders = [os.path.join(self.selected_root_folder, d) for d in os.listdir(self.selected_root_folder) if os.path.isdir(os.path.join(self.selected_root_folder, d)) and d.startswith('dump_')]
            if not subfolders:
                self.log_to_gui("오류: 'dump_'로 시작하는 하위 폴더가 없습니다.\n")
                return
            latest_folder = max(subfolders, key=os.path.getctime)
            self.log_to_gui(f"-> 대상 폴더: '{os.path.basename(latest_folder)}'\n")
            mysql_folder_path = os.path.join(latest_folder, 'mysql')
            if not os.path.isdir(mysql_folder_path):
                self.log_to_gui(f"오류: '{os.path.basename(latest_folder)}' 폴더 안에 'mysql' 폴더가 없습니다.\n")
                return
            sql_files = sorted(glob.glob(os.path.join(mysql_folder_path, "*.sql")))
            if not sql_files:
                self.log_to_gui(f"경고: 'mysql' 폴더에서 처리할 .sql 파일을 찾지 못했습니다.\n")
                return

            total_files = len(sql_files)
            self.log_to_gui(f"-> 총 {total_files}개의 .sql 파일을 찾았습니다. 업로드를 시작합니다.\n")
            self.log_to_gui("-" * 50 + "\n")

            for i, file_path in enumerate(sql_files):
                base_filename = os.path.basename(file_path)

                if base_filename == "trade_history.mysql.sql":
                    self.log_to_gui(f"[{i+1}/{total_files}] 건너뜀: {base_filename}\n")
                    skipped_count += 1
                    continue

                self.log_to_gui(f"[{i+1}/{total_files}] 처리 중: {base_filename} ...")
                
                try:
                    execute_sql_from_file(file_path)
                    self.log_to_gui(" 성공\n")
                    success_count += 1
                except Exception as e:
                    self.log_to_gui(" 실패 (로그 파일 참조)\n")
                    failure_count += 1
                    with open(log_filename, 'a', encoding='utf-8') as log_file:
                        log_file.write(f"--- ERROR processing file: {base_filename} ---\n")
                        log_file.write(traceback.format_exc())
                        log_file.write("\n" + "="*80 + "\n\n")

            # --- 🚨 핵심 변경점 (3): 최종 결과 요약 로그 🚨 ---
            self.log_to_gui("="*50 + "\n")
            self.log_to_gui("✨ 업로드 결과 요약 ✨\n")
            self.log_to_gui(f"총 대상 파일: {total_files - skipped_count}개\n")
            self.log_to_gui(f"  - 성공: {success_count}개\n")
            self.log_to_gui(f"  - 실패: {failure_count}개\n")
            self.log_to_gui(f"  - 건너뜀: {skipped_count}개\n")

            if failure_count > 0:
                self.log_to_gui(f"\n오류 상세 내용은 아래 로그 파일을 확인하세요:\n{log_filename}\n")
            else:
                self.log_to_gui("\n모든 파일 처리가 성공적으로 완료되었습니다!\n")

        except Exception as e:
            self.log_to_gui(f"\n!!! 작업 시작 중 심각한 오류 발생: {e} !!!\n")

    def check_thread(self, thread):
        if thread.is_alive():
            self.master.after(100, self.check_thread, thread)
        else:
            self.on_upload_complete()
            
    def on_upload_complete(self):
        self.upload_button.config(state="normal")
        self.select_button.config(state="normal")
        messagebox.showinfo("완료", "데이터베이스 업로드 작업이 완료되었습니다.")

    def log_to_gui(self, message):
        self.status_text.config(state='normal')
        self.status_text.insert(tk.END, message)
        self.status_text.see(tk.END)
        self.status_text.config(state='disabled')
        self.master.update_idletasks()

    def clear_gui_log(self):
        self.status_text.config(state='normal')
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state='disabled')

if __name__ == "__main__":
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()
