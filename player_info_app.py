# 파일명: player_info_app.py (최종 수정본)

from flask import Flask, render_template, request, redirect, url_for
import pymysql
import os
from dotenv import load_dotenv
import json

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

# --- 데이터 조회 함수들 ---

def get_player_data():
    connection = get_db_connection()
    if connection is None: return []
    try:
        with connection.cursor() as cursor:
            # 이 함수는 기존과 동일하게 유지
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
    # 이 함수는 수정하지 않음
    connection = get_db_connection()
    if connection is None: return []
    try:
        with connection.cursor() as cursor:
            sql = """
            SELECT 
                a.player_id,
                CASE WHEN a.nation_id = '177' THEN CONCAT(a.last_name, a.first_name) ELSE CONCAT(a.first_name, ' ', a.last_name) END AS name,
                CASE a.position WHEN 1 THEN '투수' WHEN 2 THEN '포수' WHEN 3 THEN '1루수' WHEN 4 THEN '2루수' WHEN 5 THEN '3루수' WHEN 6 THEN '유격수' WHEN 7 THEN '좌익수' WHEN 8 THEN '중견수' WHEN 9 THEN '우익수' WHEN 10 THEN '지명타자' ELSE '기타' END AS position_name,
                c.name AS team_name, a.age,
                CASE a.bats WHEN 1 THEN '우타' WHEN 2 THEN '좌타' ELSE '양타' END AS bat,
                CASE a.throws WHEN 1 THEN '우투' WHEN 2 THEN '좌투' ELSE '양투' END AS throws,
                a.personality_work_ethic, a.personality_intelligence, a.personality_leader, a.personality_loyalty, a.personality_play_for_winner, a.personality_greed,
                a.injury_is_injured, a.injury_left, a.prone_overall, a.rust, a.morale, a.morale_player_role, a.expectation
            FROM players a, players_roster_status b, teams c
            WHERE b.trade_status != 0 
              AND a.player_id = b.player_id 
              AND a.team_id = c.team_id
              and c.league_id in ('221', '222')
              and a.nation_id = '177'
            ORDER BY c.name, a.position;
            """
            cursor.execute(sql)
            return cursor.fetchall()
    finally:
        if connection: connection.close()


# [수정] 신인 드래프트 대상 선수 조회 함수
def get_draft_eligible_players():
    connection = get_db_connection()
    if connection is None: return []
    try:
        with connection.cursor() as cursor:
            # get_player_data와 동일한 컬럼 구조로 맞춤
            sql = """
            SELECT
                a.player_id, 
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
            FROM players a
            WHERE a.draft_eligible = 1
              AND a.nation_id = '177' 
            ORDER BY a.team_id, a.position;
            """
            cursor.execute(sql)
            return cursor.fetchall()
    finally:
        if connection: connection.close()

# [추가] FA 선수 조회 함수
def get_fa_players():
    connection = get_db_connection()
    if connection is None: return []
    try:
        with connection.cursor() as cursor:
            # team_id가 0인 선수 (FA) 조회
            sql = """
            SELECT
                a.player_id, 
                CASE a.position WHEN 1 THEN '투수' WHEN 2 THEN '포수' WHEN 3 THEN '1루수' WHEN 4 THEN '2루수' WHEN 5 THEN '3루수' WHEN 6 THEN '유격수' WHEN 7 THEN '좌익수' WHEN 8 THEN '중견수' WHEN 9 THEN '우익수' WHEN 10 THEN '지명타자' ELSE '기타' END AS position_name,
                CASE WHEN a.nation_id = '177' THEN CONCAT(a.last_name, a.first_name) ELSE CONCAT(a.first_name, ' ', a.last_name) END AS name,
                a.age,
                CASE a.bats WHEN 1 THEN '우타' WHEN 2 THEN '좌타' WHEN 3 THEN '양타' ELSE '기타' END AS bat,
                CASE a.throws WHEN 1 THEN '우투' WHEN 2 THEN '좌투' WHEN 3 THEN '양투' ELSE '기타' END AS throws,
                a.personality_work_ethic, a.personality_intelligence,
                (a.personality_work_ethic + a.personality_intelligence) AS work_intel_sum,
                a.personality_leader, a.personality_loyalty, a.personality_play_for_winner, a.personality_greed,
                a.injury_is_injured, a.injury_left, a.prone_overall, a.rust, a.morale, a.morale_player_role, a.expectation
            FROM players a
            WHERE a.team_id = 0
              AND a.nation_id = '177' -- 한국 선수만 조회 (필요시 제거 가능)
            ORDER BY a.position;
            """
            cursor.execute(sql)
            return cursor.fetchall()
    finally:
        if connection: connection.close()

# [추가] 선수의 최근 3년 성적 조회 함수
def get_player_recent_stats(player_id, position):
    connection = get_db_connection()
    if connection is None: return []
    
    stats = []
    try:
        with connection.cursor() as cursor:
            # position 값을 안전하게 정수로 변환
            try:
                pos_int = int(position)
            except (ValueError, TypeError):
                pos_int = 0

            if pos_int == 1: # 투수 (Pitcher)
                # 투수 최근 3년 기록 (승, 패, 세이브, 방어율 등)
                sql = """
                SELECT s.year, s.level_id, s.g, s.w, s.l, s.s, s.ip,
                       ROUND((s.er * 9) / NULLIF(s.ip, 0), 2) as era, 
                       t.name as team_name
                FROM players_career_pitching_stats s
                LEFT JOIN teams t ON s.team_id = t.team_id
                WHERE s.player_id = %s AND s.split_id = 1
                ORDER BY s.year DESC
                LIMIT 10
                """
            else: # 타자 (Batter)
                # 타자 최근 3년 기록 (타율 계산 포함)
                sql = """
                SELECT s.year, s.level_id, s.g, s.ab, s.h, s.hr, s.rbi, 
                       ROUND(s.h / NULLIF(s.ab, 0), 3) as avg, t.name as team_name
                FROM players_career_batting_stats s
                LEFT JOIN teams t ON s.team_id = t.team_id
                WHERE s.player_id = %s AND s.split_id = 1
                ORDER BY s.year DESC
                LIMIT 10
                """
            cursor.execute(sql, (player_id,))
            stats = cursor.fetchall()
    except Exception as e:
        print(f"성적 조회 중 오류 (테이블이 없거나 컬럼 불일치): {e}")
        stats = []
    finally:
        if connection: connection.close()
    return stats

# [추가] 데이터 기준일 조회 함수
def get_data_base_date():
    config_file = os.path.join(os.path.expanduser('~'), '.ootp_uploader_config.json')
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                root_path = config.get('last_path')
                
                if root_path and os.path.isdir(root_path):
                    # dump_ 로 시작하는 폴더 찾기
                    subfolders = [os.path.join(root_path, d) for d in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, d)) and d.startswith('dump_')]
                    if subfolders:
                        # 최신 폴더 찾기 (생성시간 기준)
                        latest_folder = max(subfolders, key=os.path.getctime)
                        folder_name = os.path.basename(latest_folder)
                        
                        # dump_YYYY_MM 형식 파싱 (예: dump_2025_03 -> 25년 3월)
                        parts = folder_name.split('_')
                        if len(parts) >= 3:
                            year = parts[1]
                            month = parts[2]
                            display_str = f"기준 : {year[2:]}년 {int(month)}월"
                            if len(parts) >= 4: # 일(Day)까지 있는 경우
                                display_str += f" {int(parts[3])}일"
                            return display_str
    except Exception:
        pass
    return "기준 : 날짜 정보 없음"

# [추가] 선수 상세 정보 조회 (ID로 조회) - 재사용을 위해 분리
def get_player_details(player_id):
    connection = get_db_connection()
    if connection is None: return None
    try:
        with connection.cursor() as cursor:
            sql = """
            SELECT 
                a.*, 
                IFNULL(b.name, 'FA') as team_name,
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
            LEFT JOIN teams b ON a.team_id = b.team_id
            WHERE a.player_id = %s
            """
            cursor.execute(sql, (player_id,))
            return cursor.fetchone()
    finally:
        if connection: connection.close()

# [수정] 이름으로 선수 찾기 (여러 명 반환 가능하도록 수정)
def find_players_by_name(name):
    connection = get_db_connection()
    if connection is None: return []
    try:
        with connection.cursor() as cursor:
            sql = """
            SELECT 
                a.player_id,
                CASE WHEN a.nation_id = '177' THEN CONCAT(a.last_name, a.first_name) ELSE CONCAT(a.first_name, ' ', a.last_name) END AS full_name,
                IFNULL(b.name, 'FA') as team_name,
                CASE a.position WHEN 1 THEN '투수' WHEN 2 THEN '포수' WHEN 3 THEN '1루수' WHEN 4 THEN '2루수' WHEN 5 THEN '3루수' WHEN 6 THEN '유격수' WHEN 7 THEN '좌익수' WHEN 8 THEN '중견수' WHEN 9 THEN '우익수' WHEN 10 THEN '지명타자' ELSE '기타' END AS position_name,
                a.age
            FROM players a
            LEFT JOIN teams b ON a.team_id = b.team_id
            WHERE CONCAT(a.last_name, a.first_name) LIKE %s OR CONCAT(a.first_name, ' ', a.last_name) LIKE %s OR a.first_name LIKE %s OR a.last_name LIKE %s
            """
            like_query = f"%{name}%"
            cursor.execute(sql, (like_query, like_query, like_query, like_query))
            return cursor.fetchall()
    finally:
        if connection: connection.close()

# --- 라우트(경로) 설정 (이하 동일) ---

@app.route('/')
def show_players():
    connection = get_db_connection()
    if connection is None:
        return "데이터베이스 연결에 실패했습니다.", 500

    try:
        with connection.cursor() as cursor:
            # 한화 선수단 조회 (team_id = 140 가정)
            sql_hanwha = """
            SELECT 
                a.player_id, a.uniform_number, b.name AS team_name,
                CASE a.position WHEN 1 THEN '투수' WHEN 2 THEN '포수' WHEN 3 THEN '1루수' WHEN 4 THEN '2루수' WHEN 5 THEN '3루수' WHEN 6 THEN '유격수' WHEN 7 THEN '좌익수' WHEN 8 THEN '중견수' WHEN 9 THEN '우익수' WHEN 10 THEN '지명타자' ELSE '기타' END AS position_name,
                CASE WHEN a.nation_id = '177' THEN CONCAT(a.last_name, a.first_name) ELSE CONCAT(a.first_name, ' ', a.last_name) END AS name,
                a.age,
                CASE a.bats WHEN 1 THEN '우타' WHEN 2 THEN '좌타' WHEN 3 THEN '양타' ELSE '기타' END AS bat,
                CASE a.throws WHEN 1 THEN '우투' WHEN 2 THEN '좌투' WHEN 3 THEN '양투' ELSE '기타' END AS throws,
                a.personality_work_ethic, a.personality_intelligence,
                (a.personality_work_ethic + a.personality_intelligence) AS work_intel_sum,
                a.personality_leader, a.personality_loyalty, a.personality_play_for_winner, a.personality_greed,
                a.injury_is_injured, a.injury_left, a.prone_overall, a.rust, a.morale, a.morale_player_role, a.expectation
            FROM players a JOIN teams b ON a.team_id = b.team_id
            WHERE a.team_id = 140 
            ORDER BY a.position;
            """
            cursor.execute(sql_hanwha)
            hanwha_players = cursor.fetchall()

            # 서산 선수단 조회 (team_id = 154 가정)
            sql_seosan = """
            SELECT 
                a.player_id, a.uniform_number, b.name AS team_name,
                CASE a.position WHEN 1 THEN '투수' WHEN 2 THEN '포수' WHEN 3 THEN '1루수' WHEN 4 THEN '2루수' WHEN 5 THEN '3루수' WHEN 6 THEN '유격수' WHEN 7 THEN '좌익수' WHEN 8 THEN '중견수' WHEN 9 THEN '우익수' WHEN 10 THEN '지명타자' ELSE '기타' END AS position_name,
                CASE WHEN a.nation_id = '177' THEN CONCAT(a.last_name, a.first_name) ELSE CONCAT(a.first_name, ' ', a.last_name) END AS name,
                a.age,
                CASE a.bats WHEN 1 THEN '우타' WHEN 2 THEN '좌타' WHEN 3 THEN '양타' ELSE '기타' END AS bat,
                CASE a.throws WHEN 1 THEN '우투' WHEN 2 THEN '좌투' WHEN 3 THEN '양투' ELSE '기타' END AS throws,
                a.personality_work_ethic, a.personality_intelligence,
                (a.personality_work_ethic + a.personality_intelligence) AS work_intel_sum,
                a.personality_leader, a.personality_loyalty, a.personality_play_for_winner, a.personality_greed,
                a.injury_is_injured, a.injury_left, a.prone_overall, a.rust, a.morale, a.morale_player_role, a.expectation
            FROM players a JOIN teams b ON a.team_id = b.team_id
            WHERE a.team_id = 154
            ORDER BY a.position;
            """
            cursor.execute(sql_seosan)
            seosan_players = cursor.fetchall()

    except Exception as e:
        print(f"선수 데이터 조회 중 오류 발생: {e}")
        hanwha_players, seosan_players = [], []
    finally:
        if connection:
            connection.close()

    base_date = get_data_base_date()
    return render_template('index.html', hanwha_players=hanwha_players, seosan_players=seosan_players, base_date=base_date)

@app.route('/trade_block')
def show_trade_block():
    players = get_trade_block_players()
    return render_template('trade_block.html', players=players)

@app.route('/draft_eligible')
def show_draft_eligible():
    players = get_draft_eligible_players()
    return render_template('draft_eligible.html', players=players)

@app.route('/fa_players')
def show_fa_players():
    players = get_fa_players()
    return render_template('fa_players.html', players=players)

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
                IFNULL(b.name, 'FA') as team_name,
                CASE a.position WHEN 1 THEN '투수' WHEN 2 THEN '포수' WHEN 3 THEN '1루수' WHEN 4 THEN '2루수' WHEN 5 THEN '3루수' WHEN 6 THEN '유격수' WHEN 7 THEN '좌익수' WHEN 8 THEN '중견수' WHEN 9 THEN '우익수' WHEN 10 THEN '지명타자' ELSE '기타' END AS position_name,
                a.age
            FROM players a
            LEFT JOIN teams b ON a.team_id = b.team_id
            WHERE CONCAT(a.last_name, a.first_name) LIKE %s OR CONCAT(a.first_name, ' ', a.last_name) LIKE %s OR a.first_name LIKE %s OR a.last_name LIKE %s
            """
            like_query = f"%{player_name}%"
            cursor.execute(sql, (like_query, like_query, like_query, like_query))
            players = cursor.fetchall()

        if not players:
            return f"'{player_name}' 선수를 찾을 수 없습니다.", 404
        elif len(players) == 1:
            player_id = players[0]['player_id']
            return redirect(url_for('show_player_by_id', player_id=player_id))
        else:
            return render_template('select_player.html', players=players, search_name=player_name)

    except Exception as e:
        print(f"SEARCH ERROR: {e}")
        return f"선수 검색 중 오류가 발생했습니다: {e}", 500
    finally:
        if connection: connection.close()

# [추가] 선수 비교 페이지 라우트
@app.route('/compare')
def compare_players():
    p1_id = request.args.get('p1')
    p2_id = request.args.get('p2')
    name1 = request.args.get('name1')
    name2 = request.args.get('name2')

    # 검색어가 들어오면 ID를 찾아 리다이렉트
    if name1:
        players = find_players_by_name(name1)
        if not players:
            return f"'{name1}' 선수를 찾을 수 없습니다. <a href='/compare?p1={p1_id or ''}&p2={p2_id or ''}'>돌아가기</a>"
        elif len(players) == 1:
            return redirect(url_for('compare_players', p1=players[0]['player_id'], p2=p2_id))
        else:
            return render_template('select_player_compare.html', players=players, target='p1', other_id=p2_id, search_name=name1)
            
    if name2:
        players = find_players_by_name(name2)
        if not players:
            return f"'{name2}' 선수를 찾을 수 없습니다. <a href='/compare?p1={p1_id or ''}&p2={p2_id or ''}'>돌아가기</a>"
        elif len(players) == 1:
            return redirect(url_for('compare_players', p1=p1_id, p2=players[0]['player_id']))
        else:
            return render_template('select_player_compare.html', players=players, target='p2', other_id=p1_id, search_name=name2)

    player1 = get_player_details(p1_id) if p1_id else None
    player2 = get_player_details(p2_id) if p2_id else None
    
    stats1 = get_player_recent_stats(p1_id, player1['position']) if player1 else []
    stats2 = get_player_recent_stats(p2_id, player2['position']) if player2 else []
    
    return render_template('compare_players.html', p1=player1, p2=player2, s1=stats1, s2=stats2)

@app.route('/player/id/<int:player_id>')
def show_player_by_id(player_id):
    try:
        # 기존 로직을 함수 호출로 대체
        player = get_player_details(player_id)

        if player:
            # [수정] 선수 정보와 함께 최근 성적도 조회하여 템플릿으로 전달
            # player['position']이 1이면 투수, 그 외는 타자로 처리
            stats = get_player_recent_stats(player_id, player['position'])
            return render_template('player_info.html', player=player, stats=stats)
        else:
            return "해당 ID의 선수를 찾을 수 없습니다.", 404
    except Exception as e:
        print(f"PLAYER_BY_ID ERROR: {e}")
        return f"선수 정보 조회 중 오류가 발생했습니다: {e}", 500

if __name__ == '__main__':
    app.run(debug=True, port=5003)
