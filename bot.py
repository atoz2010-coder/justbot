import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
import sqlite3
import datetime

load_dotenv()

# --- SQLite 설정 ---
DB_FILE = "rp_server_data.db"


def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


# 데이터베이스 초기화 (모든 봇의 테이블 생성)
def initialize_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 공통 테이블: 봇 상태
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS bot_status
                   (
                       bot_name
                       TEXT
                       PRIMARY
                       KEY,
                       last_heartbeat
                       TEXT
                       NOT
                       NULL,
                       status
                       TEXT
                       NOT
                       NULL,
                       message
                       TEXT
                       NOT
                       NULL,
                       guild_count
                       INTEGER
                       NOT
                       NULL
                   )
                   """)
    # 공통 테이블: 서버별 설정 (ticket 관련 필드 추가)
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS server_configs
                   (
                       guild_id
                       TEXT
                       PRIMARY
                       KEY,
                       registration_channel_id
                       TEXT,
                       car_admin_channel_id
                       TEXT,
                       car_admin_role_id
                       TEXT,
                       approved_cars_channel_id
                       TEXT,
                       insurance_admin_role_id
                       TEXT,
                       insurance_notification_channel_id
                       TEXT,
                       ticket_open_channel_id
                       TEXT,
                       ticket_category_id
                       TEXT,
                       ticket_staff_role_id
                       TEXT
                   )
                   """)
    # 은행 계좌 테이블
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS bank_accounts
                   (
                       user_id
                       TEXT
                       PRIMARY
                       KEY,
                       username
                       TEXT
                       NOT
                       NULL,
                       balance
                       INTEGER
                       NOT
                       NULL
                       DEFAULT
                       0
                   )
                   """)
    # 차량 등록 테이블 (car_type, purchase_date 컬럼 삭제)
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS car_registrations
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       user_id
                       TEXT
                       NOT
                       NULL,
                       username
                       TEXT
                       NOT
                       NULL,
                       car_name
                       TEXT
                       NOT
                       NULL,
                       registration_tax
                       INTEGER
                       NOT
                       NULL,
                       status
                       TEXT
                       NOT
                       NULL,
                       requested_at
                       TEXT
                       NOT
                       NULL,
                       guild_id
                       TEXT,
                       channel_id
                       TEXT,
                       approved_by
                       TEXT,
                       approved_at
                       TEXT,
                       rejected_by
                       TEXT,
                       rejected_at
                       TEXT,
                       rejection_reason
                       TEXT,
                       timed_out_at
                       TEXT
                   )
                   """)
    # 사용자 경고 테이블
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS user_warnings
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       user_id
                       TEXT
                       NOT
                       NULL,
                       username
                       TEXT
                       NOT
                       NULL,
                       reason
                       TEXT
                       NOT
                       NULL,
                       moderator_id
                       TEXT
                       NOT
                       NULL,
                       moderator_name
                       TEXT
                       NOT
                       NULL,
                       timestamp
                       TEXT
                       NOT
                       NULL
                   )
                   """)
    # 게임 통계 테이블
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS game_stats
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       game_type
                       TEXT
                       NOT
                       NULL,
                       user_id
                       TEXT
                       NOT
                       NULL,
                       username
                       TEXT
                       NOT
                       NULL,
                       sides
                       INTEGER,
                       result
                       TEXT,
                       user_choice
                       TEXT,
                       bot_choice
                       TEXT,
                       timestamp
                       TEXT
                       NOT
                       NULL
                   )
                   """)
    # 보험 정책 테이블
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS insurance_policies
                   (
                       user_id
                       TEXT
                       PRIMARY
                       KEY,
                       username
                       TEXT
                       NOT
                       NULL,
                       type
                       TEXT
                       NOT
                       NULL,
                       status
                       TEXT
                       NOT
                       NULL,
                       expiry_date
                       TEXT
                       NOT
                       NULL,
                       joined_at
                       TEXT
                       NOT
                       NULL
                   )
                   """)
    # 보험 청구 테이블
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS insurance_claims
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       user_id
                       TEXT
                       NOT
                       NULL,
                       username
                       TEXT
                       NOT
                       NULL,
                       type
                       TEXT
                       NOT
                       NULL,
                       description
                       TEXT
                       NOT
                       NULL,
                       amount
                       INTEGER
                       NOT
                       NULL,
                       status
                       TEXT
                       NOT
                       NULL,
                       timestamp
                       TEXT
                       NOT
                       NULL,
                       guild_id
                       TEXT,
                       channel_id
                       TEXT,
                       processed_by
                       TEXT,
                       processed_by_name
                       TEXT,
                       processed_at
                       TEXT,
                       process_reason
                       TEXT
                   )
                   """)
    # 티켓 테이블 (새로 추가)
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS tickets
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       user_id
                       TEXT
                       NOT
                       NULL,
                       username
                       TEXT
                       NOT
                       NULL,
                       guild_id
                       TEXT
                       NOT
                       NULL,
                       channel_id
                       TEXT
                       NOT
                       NULL,
                       status
                       TEXT
                       NOT
                       NULL, -- open, closed, claimed, archived
                       reason
                       TEXT,
                       opened_at
                       TEXT
                       NOT
                       NULL,
                       closed_at
                       TEXT,
                       closed_by
                       TEXT
                   )
                   """)
    conn.commit()
    conn.close()
    print(f"✅ 통합 봇: SQLite 데이터베이스 '{DB_FILE}' 초기화 완료!")


# 서버별 설정 불러오는 헬퍼 함수
def get_server_config(guild_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM server_configs WHERE guild_id = ?", (str(guild_id),))
    config = cursor.fetchone()
    conn.close()
    return config


# 서버별 설정 업데이트/삽입 헬퍼 함수
def set_server_config(guild_id, config_name, config_value):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        INSERT INTO server_configs (guild_id, {config_name}) VALUES (?, ?)
        ON CONFLICT(guild_id) DO UPDATE SET {config_name} = EXCLUDED.{config_name}
    """, (str(guild_id), str(config_value)))
    conn.commit()
    conn.close()


initialize_db()

intents = discord.Intents.all()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

BOT_NAME = "통합 RP 봇"
BOT_TOKEN = os.getenv("BOT_TOKEN")


@tasks.loop(minutes=1)
async def record_bot_status():
    conn = get_db_connection()
    cursor = conn.cursor()
    status_info = {
        "bot_name": BOT_NAME,
        "last_heartbeat": datetime.datetime.utcnow().isoformat(),
        "status": "Online",
        "message": "정상 작동 중",
        "guild_count": len(bot.guilds) if bot.guilds else 0
    }
    cursor.execute("""
        INSERT OR REPLACE INTO bot_status (bot_name, last_heartbeat, status, message, guild_count)
        VALUES (?, ?, ?, ?, ?)
    """, (status_info["bot_name"], status_info["last_heartbeat"], status_info["status"], status_info["message"],
          status_info["guild_count"]))
    conn.commit()
    conn.close()


@bot.event
async def on_ready():
    print(f'🚀 {bot.user.name} 봇 준비 완료! 모든 기능 야무지게 시작합니다.')
    try:
        await bot.tree.sync()
        print("✅ 모든 슬래시 커맨드 동기화 완료!")
    except Exception as e:
        print(f"❌ 슬래시 커맨드 동기화 실패: {e}")
    record_bot_status.start()

    # Cogs 로드 시 필요한 함수들을 bot 객체에 직접 할당
    bot.get_server_config = get_server_config
    bot.set_server_config = set_server_config
    bot.get_db_connection = get_db_connection

    cogs_to_load = [
        "cogs.bank",
        "cogs.car",
        "cogs.moderation",
        "cogs.music",
        "cogs.game",
        "cogs.insurance"
    ]
    for cog in cogs_to_load:
        try:
            await bot.load_extension(cog)
            print(f"로드 성공: {cog}")
        except Exception as e:
            print(f"로드 실패: {cog} - {e}")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    await bot.process_commands(message)


try:
    bot.run(BOT_TOKEN)
except discord.LoginFailure:
    print("❌ 봇 토큰이 올바르지 않거나 비어있습니다. 토큰을 확인해주세요!")
except Exception as e:
    print(f"❌ 봇 실행 중 예상치 못한 오류 발생: {e}")