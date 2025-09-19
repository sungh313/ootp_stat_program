import os
from flask import Flask, render_template_string, request, jsonify
import pymysql
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

app = Flask(__name__)

# --- 데이터베이스 연결 설정 ---
try:
    conn = pymysql.connect(
        host=os.getenv('DB_HOST'), user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'),
        db=os.getenv('DB_DATABASE'), port=int(os.getenv('DB_PORT', 3306)),
        charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor
    )
    db_connection_error = None
except Exception as e:
    db_connection_error = f"데이터베이스 연결 오류: {e}"
    conn = None

# --- 공통 SQL 쿼리 필드 ---
# 메인 쿼리와 검색 쿼리에서 재사용하기 위해 필드 목록을 상수로 정의
SQL_SELECT_FIELDS = """
    a.player_id, c.name AS team_name,
    CASE a.position WHEN 1 THEN '투수' WHEN 2 THEN '포수' WHEN 3 THEN '1루수' WHEN 4 THEN '2루수' WHEN 5 THEN '3루수' WHEN 6 THEN '유격수' WHEN 7 THEN '좌익수' WHEN 8 THEN '중견수' WHEN 9 THEN '우익수' WHEN 10 THEN '지명타자' ELSE '기타' END AS position_name,
    CASE WHEN a.nation_id = 177 THEN CONCAT(a.last_name, a.first_name) ELSE CONCAT(a.first_name, ' ', a.last_name) END AS name,
    CONCAT(a.age, "세") AS age,
    CASE a.bats WHEN 1 THEN "우타" WHEN 2 THEN "좌타" WHEN 3 THEN "양타" ELSE "기타" END AS bat,
    CASE a.throws WHEN 1 THEN "우투" WHEN 2 THEN "좌투" WHEN 3 THEN "양투" ELSE "기타" END AS throws,
    d.running_ratings_speed, d.batting_ratings_overall_contact, d.batting_ratings_talent_contact, d.batting_ratings_overall_power, d.batting_ratings_talent_power,
    d.batting_ratings_overall_eye, d.batting_ratings_talent_eye, d.batting_ratings_overall_gap, d.batting_ratings_talent_gap, d.batting_ratings_overall_strikeouts,
    d.batting_ratings_talent_strikeouts, d.batting_ratings_misc_bunt, d.batting_ratings_misc_bunt_for_hit, a.prone_overall, a.expectation, a.rust, a.local_pop, a.national_pop,
    a.personality_work_ethic, a.personality_leader, a.personality_greed, a.personality_loyalty, a.personality_play_for_winner, a.personality_intelligence,
    a.morale, a.morale_player_performance, a.morale_team_performance, a.morale_team_transactions, a.morale_team_chemistry, a.morale_player_role
"""
SQL_FROM_JOIN = """
    FROM players a JOIN teams c ON a.team_id = c.team_id LEFT JOIN players_batting d ON a.player_id = d.player_id
"""

# --- HTML 템플릿 ---
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>선수 정보 시스템</title>
    <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
    <style>
        body { font-family: 'Malgun Gothic', sans-serif; padding: 20px; background-color: #f8f9fa; }
        h1, h2 { text-align: center; color: #333; }
        h1 { color: #FF6600; }
        .section-container { margin-bottom: 25px; padding: 20px; background-color: #fff; border-radius: .25rem; box-shadow: 0 0 10px rgba(0,0,0,0.05); }
        input, select, button { margin-right: 10px; padding: 8px; border-radius: 4px; border: 1px solid #ccc; font-size: 14px; }
        button { cursor: pointer; background-color: #007bff; color: white; border-color: #007bff; }
        .table-container { overflow-x: auto; }
        table.dataTable { width: 100% !important; min-width: 2400px; }
        table.dataTable thead th { background-color: #e9ecef; white-space: nowrap; cursor: pointer; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: center; vertical-align: middle; font-size: 12px; }
        .rating-cell { width: 130px; } .numeric-cell { font-weight: 500; min-width: 50px; }
        .bar-container { width: 100%; height: 16px; background-color: #e9ecef; border-radius: 4px; position: relative; overflow: hidden; margin: 0 auto; }
        .bar { height: 100%; position: absolute; top: 0; left: 0; border-radius: 4px; }
        .bar-label { font-size: 11px; margin-top: 4px; color: #343a40; }
        .dataTables_wrapper .dataTables_filter { display: none; } /* DataTables 기본 검색창 숨기기 */
    </style>
</head>
<body>
    <h1>🦅 선수 정보 시스템</h1>

    <div class="section-container">
        <h2>전체 선수 검색</h2>
        <input type="text" id="globalNameSearch" placeholder="선수 이름 입력">
        <button id="globalSearchBtn">검색</button>
        <div id="searchResults" class="table-container" style="margin-top: 20px;"></div>
    </div>

    <div class="section-container">
        <h2>한화 이글스 / 서산 선수단 상세 정보</h2>
        <div class="filter-controls">
            <strong>필터:</strong>
            <input type="text" id="teamNameSearch" placeholder="이름으로 필터링">
            <select id="positionFilter">
                <option value="">모든 포지션</option>
                <option>투수</option><option>포수</option><option>1루수</option><option>2루수</option><option>3루수</option>
                <option>유격수</option><option>좌익수</option><option>중견수</option><option>우익수</option><option>지명타자</option><option>기타</option>
            </select>
        </div>
        <div class="table-container" style="margin-top: 20px;">
            {% if error %} <div class="error"><strong>오류:</strong><br>{{ error|safe }}</div> {% endif %}
            <table id="playerTable" class="display">
                <thead>
                    <tr>
                        <th>이름</th><th>팀</th><th>포지션</th><th>나이</th><th>투/타</th><th class="numeric-cell">주력</th>
                        <th class="rating-cell">컨택</th><th class="rating-cell">파워</th><th class="rating-cell">선구안</th>
                        <th class="rating-cell">장타</th><th class="rating-cell">삼진회피</th><th class="rating-cell">번트</th>
                        <th>부상</th><th>기대치</th><th>Rust</th><th>지역인기</th><th>국내인기</th>
                        <th>성실성</th><th>리더십</th><th>탐욕</th><th>충성심</th><th>승부욕</th><th>지능</th>
                        <th>사기(종합)</th><th>(성적)</th><th>(팀)</th><th>(이적)</th><th>(화합)</th><th>(역할)</th>
                    </tr>
                </thead>
                <tbody>
                    {% for p in players %}
                    <!-- 메인 테이블 선수 데이터 행 (이전과 동일) -->
                    <tr>
                        <td>{{ p.name }}</td><td>{{ p.team_name }}</td><td>{{ p.position_name }}</td><td>{{ p.age }}</td><td>{{ p.throws }}/{{ p.bat }}</td>
                        <td class="numeric-cell">{{ p.running_ratings_speed if p.running_ratings_speed is not none else '-' }}</td>
                        {% macro render_rating_bar(overall, talent) %}
                            {% if overall is not none and talent is not none %}{% set color = '' %}{% if overall < 30 %}{% set color = '#dc3545' %}{% elif overall < 40 %}{% set color = '#fd7e14' %}{% elif overall < 50 %}{% set color = '#ffc107' %}{% elif overall < 60 %}{% set color = '#28a745' %}{% elif overall < 70 %}{% set color = '#17a2b8' %}{% else %}{% set color = '#007bff' %}{% endif %}<div class="bar-container"><div class="bar" style="width: {{ (talent/100)*100 }}%; background-color: {{ color }}; opacity: 0.4;"></div><div class="bar" style="width: {{ (overall/100)*100 }}%; background-color: {{ color }};"></div></div><div class="bar-label">{{ overall }} / {{ talent }}</div>{% else %} - {% endif %}
                        {% endmacro %}
                        <td>{{ render_rating_bar(p.batting_ratings_overall_contact, p.batting_ratings_talent_contact) }}</td>
                        <td>{{ render_rating_bar(p.batting_ratings_overall_power, p.batting_ratings_talent_power) }}</td>
                        <td>{{ render_rating_bar(p.batting_ratings_overall_eye, p.batting_ratings_talent_eye) }}</td>
                        <td>{{ render_rating_bar(p.batting_ratings_overall_gap, p.batting_ratings_talent_gap) }}</td>
                        <td>{{ render_rating_bar(p.batting_ratings_overall_strikeouts, p.batting_ratings_talent_strikeouts) }}</td>
                        <td>{% if p.batting_ratings_misc_bunt is not none and p.batting_ratings_misc_bunt_for_hit is not none %}<div class="bar-label">{{ p.batting_ratings_misc_bunt }}/{{ p.batting_ratings_misc_bunt_for_hit }}</div>{% else %} - {% endif %}</td>
                        <td class="numeric-cell">{{ p.prone_overall if p.prone_overall is not none else '-' }}</td><td class="numeric-cell">{{ p.expectation if p.expectation is not none else '-' }}</td><td class="numeric-cell">{{ p.rust if p.rust is not none else '-' }}</td><td class="numeric-cell">{{ p.local_pop if p.local_pop is not none else '-' }}</td><td class="numeric-cell">{{ p.national_pop if p.national_pop is not none else '-' }}</td>
                        <td class="numeric-cell">{{ p.personality_work_ethic if p.personality_work_ethic is not none else '-' }}</td><td class="numeric-cell">{{ p.personality_leader if p.personality_leader is not none else '-' }}</td><td class="numeric-cell">{{ p.personality_greed if p.personality_greed is not none else '-' }}</td><td class="numeric-cell">{{ p.personality_loyalty if p.personality_loyalty is not none else '-' }}</td><td class="numeric-cell">{{ p.personality_play_for_winner if p.personality_play_for_winner is not none else '-' }}</td><td class="numeric-cell">{{ p.personality_intelligence if p.personality_intelligence is not none else '-' }}</td>
                        <td class="numeric-cell">{{ p.morale if p.morale is not none else '-' }}</td><td class="numeric-cell">{{ p.morale_player_performance if p.morale_player_performance is not none else '-' }}</td><td class="numeric-cell">{{ p.morale_team_performance if p.morale_team_performance is not none else '-' }}</td><td class="numeric-cell">{{ p.morale_team_transactions if p.morale_team_transactions is not none else '-' }}</td><td class="numeric-cell">{{ p.morale_team_chemistry if p.morale_team_chemistry is not none else '-' }}</td><td class="numeric-cell">{{ p.morale_player_role if p.morale_player_role is not none else '-' }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <script src="https://code.jquery.com/jquery-3.7.0.js"></script>
    <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
    <script>
    // --- Helper Functions for Dynamic Table ---
    function createRatingBar(overall, talent) {
        if (overall === null || talent === null) return '-';
        let color = '';
        if (overall < 30) color = '#dc3545'; else if (overall < 40) color = '#fd7e14'; else if (overall < 50) color = '#ffc107';
        else if (overall < 60) color = '#28a745'; else if (overall < 70) color = '#17a2b8'; else color = '#007bff';
        const talentWidth = (talent / 100) * 100;
        const overallWidth = (overall / 100) * 100;
        return `<div class="bar-container"><div class="bar" style="width: \${talentWidth}%; background-color: \${color}; opacity: 0.4;"></div><div class="bar" style="width: \${overallWidth}%; background-color: \${color};"></div></div><div class="bar-label">\${overall} / \${talent}</div>`;
    }
    const nullCheck = val => (val !== null && val !== undefined) ? val : '-';

    $(document).ready(function() {
        // --- Main Table (Hanwha/Seosan) Initialization ---
        var mainTable = $('#playerTable').DataTable({
            "paging": false, 
            "info": false, 
            "autoWidth": false,
            "ordering": true,  // 정렬 기능 활성화
            language: { 
                "emptyTable": "표시할 데이터가 없습니다.",
                "sortAscending": ": 오름차순 정렬",
                "sortDescending": ": 내림차순 정렬"
            }
        });
        
        // 이름 검색 기능
        $('#teamNameSearch').on('keyup', function() {
            mainTable.search(this.value).draw();
        });
        
        // 포지션 필터링
        $('#positionFilter').on('change', function() {
            var val = $(this).val();
            mainTable.column(2).search(val).draw();
        });

        var searchTable; // 검색 테이블 인스턴스를 저장할 변수

        // --- Global Player Search ---
        $('#globalSearchBtn').on('click', function() {
            var playerName = $('#globalNameSearch').val();
            var resultsDiv = $('#searchResults');
            if (playerName.trim() === '') { resultsDiv.html('<p>검색할 선수 이름을 입력해주세요.</p>'); return; }
            resultsDiv.html('<p>검색 중...</p>');
            
            $.ajax({
                url: '/search', data: { name: playerName },
                success: function(data) {
                    // 기존 테이블이 있다면 파괴(destroy)하여 리소스를 정리
                    if(searchTable) { searchTable.destroy(); }
                    resultsDiv.empty(); // 이전 내용 지우기

                    if (data.length === 0) { resultsDiv.html('<p>검색 결과가 없습니다.</p>'); return; }
                    
                    let tableHTML = `<table id="searchResultTable" class="display"><thead><tr>
                        <th>이름</th><th>팀</th><th>포지션</th><th>나이</th><th>투/타</th><th class="numeric-cell">주력</th>
                        <th class="rating-cell">컨택</th><th class="rating-cell">파워</th><th class="rating-cell">선구안</th>
                        <th class="rating-cell">장타</th><th class="rating-cell">삼진회피</th><th class="rating-cell">번트</th>
                        <th>부상</th><th>기대치</th><th>Rust</th><th>지역인기</th><th>국내인기</th>
                        <th>성실성</th><th>리더십</th><th>탐욕</th><th>충성심</th><th>승부욕</th><th>지능</th>
                        <th>사기(종합)</th><th>(성적)</th><th>(팀)</th><th>(이적)</th><th>(화합)</th><th>(역할)</th>
                        </tr></thead><tbody>`;
                    
                    data.forEach(p => {
                        tableHTML += '<tr>' +
                            `<td>\${p.name}</td><td>\${p.team_name}</td><td>\${p.position_name}</td><td>\${p.age}</td><td>\${p.throws}/\${p.bat}</td>` +
                            `<td class="numeric-cell">\${nullCheck(p.running_ratings_speed)}</td>` +
                            `<td>\${createRatingBar(p.batting_ratings_overall_contact, p.batting_ratings_talent_contact)}</td>` +
                            `<td>\${createRatingBar(p.batting_ratings_overall_power, p.batting_ratings_talent_power)}</td>` +
                            `<td>\${createRatingBar(p.batting_ratings_overall_eye, p.batting_ratings_talent_eye)}</td>` +
                            `<td>\${createRatingBar(p.batting_ratings_overall_gap, p.batting_ratings_talent_gap)}</td>` +
                            `<td>\${createRatingBar(p.batting_ratings_overall_strikeouts, p.batting_ratings_talent_strikeouts)}</td>` +
                            `<td>\${p.batting_ratings_misc_bunt !== null && p.batting_ratings_misc_bunt_for_hit !== null ? `<div class="bar-label">\${p.batting_ratings_misc_bunt}/\${p.batting_ratings_misc_bunt_for_hit}</div>` : '-'}</td>` +
                            [p.prone_overall, p.expectation, p.rust, p.local_pop, p.national_pop, p.personality_work_ethic, p.personality_leader, p.personality_greed, p.personality_loyalty, p.personality_play_for_winner, p.personality_intelligence, p.morale, p.morale_player_performance, p.morale_team_performance, p.morale_team_transactions, p.morale_team_chemistry, p.morale_player_role].map(val => `<td class="numeric-cell">\${nullCheck(val)}</td>`).join('') +
                            '</tr>';
                    });
                    tableHTML += '</tbody></table>';
                    resultsDiv.html(tableHTML);
                    
                    // 검색 결과 테이블에 DataTables 적용
                    searchTable = $('#searchResultTable').DataTable({
                        "paging": false,
                        "info": false,
                        "searching": false,
                        "autoWidth": false,
                        "ordering": true,  // 정렬 기능 활성화
                        language: {
                            "sortAscending": ": 오름차순 정렬",
                            "sortDescending": ": 내림차순 정렬"
                        }
                    });
                },
                error: function() { resultsDiv.html('<p>검색 중 오류가 발생했습니다.</p>'); }
            });
        });
    });
    </script>
</body>
</html>
"""

# --- Flask 라우팅 ---
@app.route('/')
def player_list():
    if db_connection_error:
        return render_template_string(html_template, error=db_connection_error, players=[])
    
    main_query = f"SELECT {SQL_SELECT_FIELDS} {SQL_FROM_JOIN} WHERE a.team_id IN (2, 16) ORDER BY c.team_id, a.position, a.last_name, a.first_name;"
    
    players = []
    try:
        if conn:
            with conn.cursor() as cursor:
                cursor.execute(main_query)
                players = cursor.fetchall()
    except Exception as e:
        return render_template_string(html_template, error=f"데이터 조회 중 오류 발생: {e}", players=[])
    return render_template_string(html_template, players=players)

@app.route('/search')
def search_players():
    player_name = request.args.get('name', '')
    if not conn or not player_name: return jsonify([])

    search_query = f"""
    SELECT {SQL_SELECT_FIELDS} {SQL_FROM_JOIN}
    WHERE (a.last_name LIKE %s OR a.first_name LIKE %s OR CONCAT(a.last_name, a.first_name) LIKE %s OR CONCAT(a.first_name, ' ', a.last_name) LIKE %s)
    LIMIT 20;
    """
    
    try:
        with conn.cursor() as cursor:
            search_term = f"%{player_name}%"
            cursor.execute(search_query, (search_term, search_term, search_term, search_term))
            results = cursor.fetchall()
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def run_app():
    app.run(debug=False, port=5001)

if __name__ == '__main__':
    run_app()
