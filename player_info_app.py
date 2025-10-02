# 파일명: player_info_app.py (최종 수정본)

from flask import Flask, render_template, request, redirect, url_for
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# --- DB 설정 및 연결 함수 (기존과 동일) ---
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'db': os.getenv('DB_DATABASE'),
    'port': 3306,
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    try:
        return pymysql.connect(**DB_CONFIG)
    except Exception as e:
        print(f"DB 연결 오류: {e}")
        return None

# --- 데이터 조회 함수들 (기존과 동일) ---
def get_player_data():
    connection = get_db_connection()
    if connection is None: return []
    try:
        with connection.cursor() as cursor:
            sql = """
            SELECT 
                a.player_id, b.name AS team_name,
                CASE a.position WHEN 1 THEN '투수' WHEN 2 THEN '포수' WHEN 3 THEN '1루수' WHEN 4 THEN '2루수' WHEN 5 THEN '3루수' WHEN 6 THEN '유격수' WHEN 7 THEN '좌익수' WHEN 8 THEN '중견수' WHEN 9 THEN '우익수' WHEN 10 THEN '지명타자' ELSE '기타' END AS position_name,
                CASE WHEN a.nation_id = '177' THEN CONCAT(a.last_name, a.first_name) ELSE CONCAT(a.first_name, ' ', a.last_name) END AS name,
                a.age,
                CASE a.bats WHEN 1 THEN '우타' WHEN 2 THEN '좌타' WHEN 3 THEN '양타' ELSE '기타' END AS bat,
                CASE a.throws WHEN 1 THEN '우투' WHEN 2 THEN '좌투' WHEN 3 THEN '양투' ELSE '기타' END AS throws,
                a.personality_work_ethic,
                a.personality_intelligence,
                (a.personality_work_ethic + a.personality_intelligence) AS work_intel_sum,
                a.personality_leader, a.personality_loyalty, a.personality_play_for_winner, a.personality_greed,
                a.injury_is_injured, a.injury_left, a.prone_overall, a.rust, a.morale, a.morale_player_role, a.expectation
            FROM players a, teams b
            WHERE a.team_id IN (2, 16) AND a.team_id = b.team_id
            ORDER BY a.team_id, a.position;
            """
            cursor.execute(sql)
            return cursor.fetchall()
    finally:
        if connection: connection.close()

def get_trade_block_players():
    # 이 함수는 수정하지 않음 (기존 코드 유지)
    connection = get_db_connection()
    if connection is None: return []
    try:
        with connection.cursor() as cursor:
            sql = """
            SELECT 
                CASE WHEN a.nation_id = '177' THEN CONCAT(a.last_name, a.first_name) ELSE CONCAT(a.first_name, ' ', a.last_name) END AS name,
                CASE a.position WHEN 1 THEN '투수' WHEN 2 THEN '포수' WHEN 3 THEN '1루수' WHEN 4 THEN '2루수' WHEN 5 THEN '3루수' WHEN 6 THEN '유격수' WHEN 7 THEN '좌익수' WHEN 8 THEN '중견수' WHEN 9 THEN '우익수' WHEN 10 THEN '지명타자' ELSE '기타' END AS position_name,
                c.name AS team_name, a.age,
                CASE a.bats WHEN 1 THEN '우타' WHEN 2 THEN '좌타' ELSE '양타' END AS bat,
                CASE a.throws WHEN 1 THEN '우투' WHEN 2 THEN '좌투' ELSE '양투' END AS throws,
                a.personality_work_ethic, a.personality_intelligence, a.personality_leader, a.personality_loyalty, a.personality_play_for_winner, a.personality_greed,
                a.injury_is_injured, a.injury_left, a.prone_overall, a.rust, a.morale, a.morale_player_role, a.expectation
            FROM players a, players_roster_status b, teams c
            WHERE b.trade_status != 0 AND a.player_id = b.player_id AND a.team_id = c.team_id
            ORDER BY c.name, a.position;
            """
            cursor.execute(sql)
            return cursor.fetchall()
    finally:
        if connection: connection.close()

# --- 라우트(경로) 설정 ---

@app.route('/')
def show_players():
    players = get_player_data()
    return render_template('index.html', players=players)

@app.route('/trade_block')
def show_trade_block():
    players = get_trade_block_players()
    return render_template('trade_block.html', players=players)

@app.route('/search')
def search_player():
    player_name = request.args.get('name', '')
    if not player_name:
        return "검색할 선수 이름을 입력해주세요.", 400

    connection = get_db_connection()
    if connection is None: return "DB 연결 실패", 500
    
    try:
        with connection.cursor() as cursor:
            sql = """
            SELECT
                a.player_id,
                CASE WHEN a.nation_id = '177' THEN CONCAT(a.last_name, a.first_name) ELSE CONCAT(a.first_name, ' ', a.last_name) END AS full_name,
                b.name as team_name,
                CASE a.position WHEN 1 THEN '투수' WHEN 2 THEN '포수' WHEN 3 THEN '1루수' WHEN 4 THEN '2루수' WHEN 5 THEN '3루수' WHEN 6 THEN '유격수' WHEN 7 THEN '좌익수' WHEN 8 THEN '중견수' WHEN 9 THEN '우익수' WHEN 10 THEN '지명타자' ELSE '기타' END AS position_name,
                a.age
            FROM players a
            JOIN teams b ON a.team_id = b.team_id
            WHERE CONCAT(a.last_name, a.first_name) LIKE %s OR CONCAT(a.first_name, ' ', a.last_name) LIKE %s OR a.first_name LIKE %s OR a.last_name LIKE %s
            """
            like_query = f"%{player_name}%"
            cursor.execute(sql, (like_query, like_query, like_query, like_query))
            players = cursor.fetchall()

        if not players:
            return f"'{player_name}' 선수를 찾을 수 없습니다.", 404
        elif len(players) == 1:
            # [수정] 결과가 한 명이면, 고유 ID 페이지로 리다이렉트
            player_id = players[0]['player_id']
            return redirect(url_for('show_player_by_id', player_id=player_id))
        else:
            return render_template('select_player.html', players=players, search_name=player_name)

    except Exception as e:
        # 오류 발생 시 터미널에 상세 오류 출력
        print(f"SEARCH ERROR: {e}")
        return f"선수 검색 중 오류가 발생했습니다: {e}", 500
    finally:
        if connection: connection.close()

# [수정] 고유 ID로 선수 정보를 보여주는 경로
@app.route('/player/id/<int:player_id>')
def show_player_by_id(player_id):
    connection = get_db_connection()
    if connection is None: return "DB 연결 실패", 500

    try:
        with connection.cursor() as cursor:
            # [수정] 완전한 SQL 쿼리로 변경
            sql = """
            SELECT 
                a.*, 
                b.name as team_name,
                CASE a.position 
                    WHEN 1 THEN '투수' WHEN 2 THEN '포수' WHEN 3 THEN '1루수' 
                    WHEN 4 THEN '2루수' WHEN 5 THEN '3루수' WHEN 6 THEN '유격수' 
                    WHEN 7 THEN '좌익수' WHEN 8 THEN '중견수' WHEN 9 THEN '우익수' 
                    WHEN 10 THEN '지명타자' ELSE '기타' 
                END AS position_name,
                CASE WHEN a.nation_id = '177' THEN CONCAT(a.last_name, a.first_name) 
                     ELSE CONCAT(a.first_name, ' ', a.last_name) 
                END AS full_name
            FROM players a
            JOIN teams b ON a.team_id = b.team_id
            WHERE a.player_id = %s
            """
            cursor.execute(sql, (player_id,))
            player = cursor.fetchone()

        if player:
            return render_template('player_info.html', player=player)
        else:
            return "해당 ID의 선수를 찾을 수 없습니다.", 404
    except Exception as e:
        print(f"PLAYER_BY_ID ERROR: {e}")
        return f"선수 정보 조회 중 오류가 발생했습니다: {e}", 500
    finally:
        if connection: connection.close()

if __name__ == '__main__':
    app.run(debug=True, port=5001)
