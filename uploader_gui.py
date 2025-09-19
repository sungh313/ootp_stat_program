# 파일명: uploader_gui.py

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading

# db_handler 모듈에서 데이터베이스 처리 함수를 가져옵니다.
from db_handler import execute_sql_from_file

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("OOTP SQL Uploader")
        self.master.geometry("600x450")
        self.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.sql_file_path = ""
        self.create_widgets()   

    def create_widgets(self):
        # 파일 선택 프레임
        file_frame = tk.Frame(self)
        file_frame.pack(fill=tk.X, pady=5)
        
        self.file_label = tk.Label(file_frame, text="선택된 파일:", width=10, anchor="w")
        self.file_label.pack(side=tk.LEFT, padx=(0, 5))

        self.path_var = tk.StringVar()
        self.path_var.set("파일을 선택해주세요.")
        self.path_entry = tk.Entry(file_frame, textvariable=self.path_var, state='readonly')
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.select_button = tk.Button(file_frame, text="파일 선택", command=self.select_file)
        self.select_button.pack(side=tk.LEFT, padx=(5, 0))

        # 업로드 버튼
        self.upload_button = tk.Button(self, text="DB에 업로드", command=self.start_upload, height=2)
        self.upload_button.pack(fill=tk.X, pady=10)
        
        # 상태 표시 스크롤 텍스트
        self.status_text = scrolledtext.ScrolledText(self, wrap=tk.WORD, state='disabled', height=15)
        self.status_text.pack(fill=tk.BOTH, expand=True)

    def select_file(self):
        filepath = filedialog.askopenfilename(
            title="SQL 파일을 선택하세요",
            filetypes=(("SQL 파일", "*.sql"), ("모든 파일", "*.*"))
        )
        if filepath:
            self.sql_file_path = filepath
            self.path_var.set(filepath)
            self.log_status(f"파일 선택됨: {self.sql_file_path.split('/')[-1]}\n")

    def start_upload(self):
        if not self.sql_file_path:
            messagebox.showwarning("경고", "먼저 SQL 파일을 선택해야 합니다.")
            return

        self.upload_button.config(state="disabled")
        self.select_button.config(state="disabled")
        self.log_status("="*50 + "\n")
        
        # 스레드를 사용하여 DB 작업을 실행
        upload_thread = threading.Thread(
            target=lambda: execute_sql_from_file(self.sql_file_path, self.log_status),
            daemon=True
        )
        upload_thread.start()
        
        # 스레드 상태를 확인하여 완료 시 GUI 업데이트
        self.master.after(100, self.check_thread, upload_thread)

    def check_thread(self, thread):
        """스레드가 살아있는지 확인하고, 끝나면 완료 처리를 합니다."""
        if thread.is_alive():
            self.master.after(100, self.check_thread, thread)
        else:
            self.on_upload_complete()
            
    def on_upload_complete(self):
        self.upload_button.config(state="normal")
        self.select_button.config(state="normal")
        messagebox.showinfo("완료", "데이터베이스 업로드 작업이 완료되었습니다.")

    def log_status(self, message):
        """상태 메시지를 ScrolledText 위젯에 추가합니다."""
        self.status_text.config(state='normal')
        self.status_text.insert(tk.END, message)
        self.status_text.see(tk.END)
        self.status_text.config(state='disabled')

#이건 왜 이럴까
if __name__ == "__main__":
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()