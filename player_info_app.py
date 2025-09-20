from flask import Flask, render_template
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

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
        connection = pymysql.connect(**DB_CONFIG)
        return connection
    except Exception as e:
        print(f"DB 연결 오류: {e}")
        return None

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
                a.personality_work_ethic, a.personality_intelligence, a.personality_leader, a.personality_loyalty, a.personality_play_for_winner, a.personality_greed,
                a.injury_is_injured, a.injury_left, a.prone_overall, a.rust, a.morale, a.morale_player_role, a.expectation
            FROM players a, teams b
            WHERE a.team_id IN (2, 16) AND a.team_id = b.team_id
            ORDER BY a.team_id, a.position;
            """
            cursor.execute(sql)
            players = cursor.fetchall()
            print(f"성공적으로 {len(players)}명의 선수 데이터를 조회했습니다.")
            return players
    except pymysql.MySQLError as e:
        print(f"선수 데이터 쿼리 실행 오류: {e}")
        return []
    finally:
        if connection: connection.close()

def get_trade_block_players():
    connection = get_db_connection()
    if connection is None: return []
    try:
        with connection.cursor() as cursor:
            sql = """
            SELECT 
                CASE WHEN a.nation_id = '177' THEN CONCAT(a.last_name, a.first_name) 
                     ELSE CONCAT(a.first_name, ' ', a.last_name) END AS name,
                CASE a.position
                    WHEN 1 THEN '투수' WHEN 2 THEN '포수' WHEN 3 THEN '1루수'
                    WHEN 4 THEN '2루수' WHEN 5 THEN '3루수' WHEN 6 THEN '유격수'
                    WHEN 7 THEN '좌익수' WHEN 8 THEN '중견수' WHEN 9 THEN '우익수'
                    WHEN 10 THEN '지명타자' ELSE '기타' 
                END AS position_name,
                c.name AS team_name, a.age,
                CASE a.bats WHEN 1 THEN '우타' WHEN 2 THEN '좌타' ELSE '양타' END AS bat,
                CASE a.throws WHEN 1 THEN '우투' WHEN 2 THEN '좌투' ELSE '양투' END AS throws,
                a.personality_work_ethic, a.personality_intelligence, a.personality_leader, 
                a.personality_loyalty, a.personality_play_for_winner, a.personality_greed,
                a.injury_is_injured, a.injury_left, a.prone_overall, a.rust, a.morale, 
                a.morale_player_role, a.expectation
            FROM players a, players_roster_status b, teams c
            WHERE b.trade_status != 0
              AND a.player_id = b.player_id
              AND a.team_id = c.team_id
            ORDER BY c.name, a.position;
            """
            cursor.execute(sql)
            return cursor.fetchall()
    finally:
        if connection: connection.close()

@app.route('/')
def show_players():
    players = get_player_data()
    return render_template('index.html', players=players)

@app.route('/trade_block')
def show_trade_block():
    players = get_trade_block_players()
    return render_template('trade_block.html', players=players)

@app.route('/player/<player_name>')
def show_single_player(player_name):
    connection = get_db_connection()
    if connection is None:
        return "데이터베이스에 연결할 수 없습니다."
    
    player = None
    try:
        with connection.cursor() as cursor:
            sql = """
            SELECT 
                a.*, 
                b.name as team_name,
                CASE a.position WHEN 1 THEN '투수' WHEN 2 THEN '포수' WHEN 3 THEN '1루수' WHEN 4 THEN '2루수' WHEN 5 THEN '3루수' WHEN 6 THEN '유격수' WHEN 7 THEN '좌익수' WHEN 8 THEN '중견수' WHEN 9 THEN '우익수' WHEN 10 THEN '지명타자' ELSE '기타' END AS position_name,
                CASE WHEN a.nation_id = '177' THEN CONCAT(a.last_name, a.first_name) ELSE CONCAT(a.first_name, ' ', a.last_name) END AS full_name
            FROM players a
            JOIN teams b ON a.team_id = b.team_id
            WHERE 
                CONCAT(a.last_name, a.first_name) LIKE %s OR 
                CONCAT(a.first_name, ' ', a.last_name) LIKE %s OR
                a.first_name LIKE %s OR
                a.last_name LIKE %s
            LIMIT 1;
            """
            like_query = f"%{player_name}%"
            cursor.execute(sql, (like_query, like_query, like_query, like_query))
            player = cursor.fetchone()

    except Exception as e:
        return f"선수 검색 중 오류 발생: {e}"
    finally:
        if connection:
            connection.close()

    if player:
        return render_template('player_info.html', player=player)
    else:
        return f"'{player_name}' 선수를 찾을 수 없습니다."

if __name__ == '__main__':
    app.run(debug=True, port=5001)

