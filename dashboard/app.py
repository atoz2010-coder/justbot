from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
import sqlite3
import datetime

load_dotenv()

# --- Flask 앱 설정 ---
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "your_flask_secret_key_for_dashboard")

# --- Flask-Login 설정 ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- SQLite 설정 ---
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rp_server_data.db")


def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


# --- 사용자 모델 (Flask-Login용) ---
class User(UserMixin):
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username

    @staticmethod
    def get(user_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username FROM dashboard_users WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()
        conn.close()
        if user_data:
            return User(user_data["id"], user_data["username"])
        return None


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


# --- 초기 관리자 계정 생성 및 DB 초기화 ---
def initialize_dashboard_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 대시보드 사용자 테이블
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS dashboard_users
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       username
                       TEXT
                       UNIQUE
                       NOT
                       NULL,
                       password
                       TEXT
                       NOT
                       NULL
                   )
                   """)
    conn.commit()

    admin_username = os.getenv("DASHBOARD_ADMIN_USERNAME", "admin")
    admin_password = os.getenv("DASHBOARD_ADMIN_PASSWORD", "your_strong_admin_password")

    cursor.execute("SELECT * FROM dashboard_users WHERE username = ?", (admin_username,))
    if not cursor.fetchone():
        hashed_password = generate_password_hash(admin_password)
        cursor.execute("INSERT INTO dashboard_users (username, password) VALUES (?, ?)",
                       (admin_username, hashed_password))
        conn.commit()
        print(f"✅ 초기 관리자 계정 '{admin_username}' 생성 완료!")
    else:
        print(f"✅ 관리자 계정 '{admin_username}' 이미 존재합니다.")
    conn.close()


# --- 라우트 정의 ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password FROM dashboard_users WHERE username = ?", (username,))
        user_data = cursor.fetchone()
        conn.close()

        if user_data and check_password_hash(user_data['password'], password):
            user = User(user_data['id'], user_data['username'])
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('유효하지 않은 사용자 이름 또는 비밀번호입니다.')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bot_status")
    raw_bot_statuses = cursor.fetchall()
    conn.close()

    bot_statuses = []
    for status_row in raw_bot_statuses:
        status = dict(status_row)

        last_heartbeat_utc = datetime.datetime.fromisoformat(status['last_heartbeat'])

        status['last_heartbeat_kst'] = (last_heartbeat_utc + datetime.timedelta(hours=9)).strftime('%Y-%m-%d %H:%M:%S')

        if datetime.datetime.utcnow() - last_heartbeat_utc > datetime.timedelta(minutes=2):
            status['status'] = "Offline"
            status['message'] = "하트비트 없음"

        bot_statuses.append(status)

    return render_template('dashboard.html', bot_statuses=bot_statuses)


@app.route('/bank')
@login_required
def bank_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bank_accounts")
    bank_accounts = cursor.fetchall()
    conn.close()
    return render_template('bank.html', bank_accounts=bank_accounts)


@app.route('/moderation')
@login_required
def moderation_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    # 경고 내역 조회
    cursor.execute(
        "SELECT user_id, username, reason, moderator_name, timestamp FROM user_warnings ORDER BY user_id, timestamp ASC")
    raw_warnings = cursor.fetchall()
    # 티켓 내역 조회
    cursor.execute("SELECT * FROM tickets ORDER BY opened_at DESC")
    tickets = cursor.fetchall()
    conn.close()

    warnings_by_user = {}
    for warning in raw_warnings:
        warning_dict = dict(warning)
        if warning_dict['user_id'] not in warnings_by_user:
            warnings_by_user[warning_dict['user_id']] = {
                "user_id": warning_dict['user_id'],
                "username": warning_dict['username'],
                "warnings": []
            }
        warnings_by_user[warning_dict['user_id']]["warnings"].append({
            "reason": warning_dict['reason'],
            "moderator_name": warning_dict['moderator_name'],
            "timestamp": datetime.datetime.fromisoformat(warning_dict['timestamp'])
        })

    warnings_list = list(warnings_by_user.values())

    # Jinja2 템플릿에 전달할 티켓 데이터 처리 (ISO 포맷을 datetime 객체로 변환)
    processed_tickets = []
    for ticket in tickets:
        ticket_dict = dict(ticket)
        ticket_dict['opened_at'] = datetime.datetime.fromisoformat(ticket_dict['opened_at'])
        if ticket_dict['closed_at']:
            ticket_dict['closed_at'] = datetime.datetime.fromisoformat(ticket_dict['closed_at'])
        processed_tickets.append(ticket_dict)

    return render_template('moderation.html', warnings=warnings_list, tickets=processed_tickets,
                           timedelta=datetime.timedelta)


@app.route('/car')
@login_required
def car_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM car_registrations ORDER BY requested_at DESC")
    cars = cursor.fetchall()
    conn.close()
    return render_template('car.html', cars=cars, timedelta=datetime.timedelta)


@app.route('/insurance')
@login_required
def insurance_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM insurance_policies ORDER BY joined_at DESC")
    policies = cursor.fetchall()
    cursor.execute("SELECT * FROM insurance_claims ORDER BY timestamp DESC")
    claims = cursor.fetchall()
    conn.close()
    return render_template('insurance.html', policies=policies, claims=claims, timedelta=datetime.timedelta)


@app.route('/game')
@login_required
def game_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM game_stats ORDER BY timestamp DESC")
    game_stats = cursor.fetchall()
    conn.close()
    return render_template('game.html', game_stats=game_stats, timedelta=datetime.timedelta)


# --- 앱 실행 ---
if __name__ == '__main__':
    initialize_dashboard_db()
    app.run(host='0.0.0.0', port=5000, debug=True)