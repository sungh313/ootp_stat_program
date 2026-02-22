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
    except pymysql.MySQLError as e:
        print(f"DB 연결 오류: {e}")
        return None

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
              AND c.league_id in '221', '222'
            ORDER BY c.name, a.position;
            """
            cursor.execute(sql)
            players = cursor.fetchall()
            print(f"성공적으로 {len(players)}명의 트레이드 블록 선수를 조회했습니다.")
            return players
    except pymysql.MySQLError as e:
        print(f"트레이드 블록 쿼리 실행 오류: {e}")
        return []
    finally:
        if connection: connection.close()

@app.route('/')
def show_trade_block():
    players = get_trade_block_players()
    return render_template('trade_block.html', players=players)

if __name__ == '__main__':
    app.run(debug=True, port=5002) # 다른 포트(5002) 사용
