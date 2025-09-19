# 파일명: db_handler.py (최종 버전)

from mysql.connector import connect, Error
from dotenv import load_dotenv
import os
import re

load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_DATABASE')
DB_PORT = os.getenv('DB_PORT', 3306)


def get_db_connection():
    try:
        connection = connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT
        )
        return connection
    except Error as e:
        raise e


def preprocess_sql_content(content):
    """SQL 파일 내용의 알려진 오류들을 자동으로 수정하는 전처리 함수입니다."""
    
    # 규칙 1: 따옴표로 감싸여 있지 않은 '없음'을 'NULL'로 변경
    content = re.sub(r"(?<!['\"])없음(?!['\"])", "NULL", content)
    
    # 규칙 2: 한글 또는 닫는 괄호 뒤에 오는 큰따옴표 두 개("")를 한 개(")로 변경
    content = re.sub(r'([\uAC00-\uD7A3\)])""', r'\1"', content)

    # 규칙 3: 데이터 안에 포함된 작은따옴표(')를 두 개('')로 만들어 이스케이프
    content = content.replace("'", "''")
    
    return content


def execute_sql_from_file(file_path):
    """하나의 SQL 파일을 읽고, 전처리한 뒤, 데이터베이스에 실행합니다."""
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                with open(file_path, 'r', encoding='utf-8') as f:
                    sql_script = f.read()

                    preprocessed_script = preprocess_sql_content(sql_script)

                    # 세미콜론으로 문장을 나누어 순차적으로 실행
                    for statement in preprocessed_script.split(';'):
                        if statement.strip():
                            cursor.execute(statement)
                            
                    connection.commit()
    except Error as e:
        raise e
    except Exception as e:
        raise e
