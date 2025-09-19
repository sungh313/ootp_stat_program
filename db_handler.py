
# 파일명: db_handler.py

import mysql.connector
from mysql.connector import Error, errorcode
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# DB 접속 정보 설정
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_DATABASE')
}

def execute_sql_from_file(filepath, status_callback):
    """
    .sql 파일의 내용을 읽어 각 SQL 구문을 개별적으로 실행하고, 진행 상황을 콜백 함수로 전달합니다.

    Args:
        filepath (str): 실행할 .sql 파일의 경로
        status_callback (function): 진행 상황 메시지를 전달할 콜백 함수
    """
    if not filepath:
        status_callback("오류: 파일이 선택되지 않았습니다.\n")
        return

    connection = None
    try:
        status_callback(f"데이터베이스에 연결을 시도합니다...\n")
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        status_callback("데이터베이스에 성공적으로 연결되었습니다.\n")

        with open(filepath, 'r', encoding='utf-8') as f:
            sql_commands = f.read().split(';')
        status_callback(f"'{os.path.basename(filepath)}' 파일에서 {len(sql_commands)}개의 명령어를 읽었습니다.\n")
        
        status_callback("SQL 명령어 실행을 시작합니다...\n")
        executed_count = 0
        for command in sql_commands:
            stripped_command = command.strip()
            if stripped_command:
                try:
                    cursor.execute(stripped_command)
                    executed_count += 1
                except Error as err:
                    # 어떤 명령어가 실패했는지 명확히 출력
                    status_callback("="*20 + " SQL 오류 발생! " + "="*20 + "\n")
                    status_callback(f"오류 종류: {err}\n")
                    status_callback(f"오류 발생 명령어:\n---\n{stripped_command}\n---\n\n")
                    # 오류가 발생하면 즉시 함수를 중단하고 롤백합니다.
                    if connection and connection.is_connected():
                        connection.rollback()
                    status_callback("오류로 인해 작업을 중단하고 롤백합니다.\n")
                    return # 함수 실행 종료

        connection.commit()
        status_callback(f"총 {executed_count}개의 명령어가 성공적으로 실행 및 커밋되었습니다.\n")

    except Error as err:
        error_message = f"데이터베이스 오류 발생: {err}\n"
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            error_message = "오류: 사용자 이름 또는 비밀번호가 잘못되었습니다.\n"
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            error_message = "오류: 데이터베이스가 존재하지 않습니다.\n"
        status_callback(error_message)
        if connection and connection.is_connected():
            connection.rollback()
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            status_callback("데이터베이스 연결이 종료되었습니다.\n")
