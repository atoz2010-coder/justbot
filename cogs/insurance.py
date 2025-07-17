import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import datetime


class Insurance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 메인 bot에서 주입된 함수들
        self.get_db_connection = bot.get_db_connection
        self.get_server_config = bot.get_server_config

    INSURANCE_COST = 10000
    INSURANCE_DURATION_DAYS = 30
    INSURANCE_BENEFITS = {
        "차량보험": 50000,
        "생명보험": 100000,
        "재산보험": 70000
    }

    @app_commands.command(name="보험가입", description="RP 서버 보험에 가입합니다.")
    @app_commands.describe(보험종류="가입할 보험 종류 (차량보험/생명보험/재산보험)")
    @app_commands.guild_only()
    async def enroll_insurance(self, interaction: discord.Interaction, 보험종류: str):
        await interaction.response.defer(ephemeral=True)

        if not interaction.guild:
            await interaction.followup.send("❌ 이 명령어는 서버(길드)에서만 사용할 수 있습니다.", ephemeral=True)
            return

        user_id = str(interaction.user.id)
        normalized_type = 보험종류.strip().lower()

        if normalized_type not in self.INSURANCE_BENEFITS:
            await interaction.followup.send(f"❌ 유효하지 않은 보험 종류입니다! '차량보험', '생명보험', '재산보험' 중 하나를 선택해주세요.", ephemeral=True)
            return

        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT type, status, expiry_date FROM insurance_policies WHERE user_id = ?", (user_id,))
        existing_policy = cursor.fetchone()

        if existing_policy and existing_policy["status"] == "가입중":
            expiry_date_str = existing_policy["expiry_date"]
            expiry_date = datetime.datetime.fromisoformat(expiry_date_str)
            if expiry_date > datetime.datetime.utcnow():
                conn.close()
                await interaction.followup.send(
                    f"❌ 이미 {existing_policy['type']}에 가입되어 있습니다! 만료일: {expiry_date.strftime('%Y년 %m월 %d일')}",
                    ephemeral=True)
                return

        expiry_date = datetime.datetime.utcnow() + datetime.timedelta(days=self.INSURANCE_DURATION_DAYS)

        cursor.execute("""
                       INSERT INTO insurance_policies (user_id, username, type, status, expiry_date, joined_at)
                       VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(user_id) DO
                       UPDATE SET
                           username = EXCLUDED.username,
                           type = EXCLUDED.type,
                           status = EXCLUDED.status,
                           expiry_date = EXCLUDED.expiry_date,
                           joined_at = EXCLUDED.joined_at
                       """, (user_id, interaction.user.display_name, normalized_type, "가입중", expiry_date.isoformat(),
                             datetime.datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()

        await interaction.followup.send(
            f"✅ {interaction.user.display_name}님, **{보험종류}**에 성공적으로 가입되었습니다! "
            f"만료일: **{expiry_date.strftime('%Y년 %m월 %d일 %H시 %M분')}**"
        )

    @app_commands.command(name="내보험", description="현재 가입된 보험 정보를 확인합니다.")
    @app_commands.guild_only()
    async def my_insurance(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        conn = self.get_db_connection()
        cursor = conn.cursor()
        user_id = str(interaction.user.id)
        cursor.execute("SELECT type, status, expiry_date, joined_at FROM insurance_policies WHERE user_id = ?",
                       (user_id,))
        insurance_info = cursor.fetchone()

        if not insurance_info or insurance_info["status"] != "가입중":
            conn.close()
            await interaction.followup.send("❌ 현재 가입된 보험이 없어요! `/보험가입`으로 가입해주세요.", ephemeral=True)
            return

        expiry_date = datetime.datetime.fromisoformat(insurance_info["expiry_date"])

        if expiry_date < datetime.datetime.utcnow():
            cursor.execute("UPDATE insurance_policies SET status = ? WHERE user_id = ?", ("만료됨", user_id))
            conn.commit()
            conn.close()
            await interaction.followup.send(
                f"❌ 가입했던 {insurance_info['type']}이(가) {expiry_date.strftime('%Y년 %m월 %d일')}부로 만료되었습니다!", ephemeral=True)
            return

        conn.close()
        embed = discord.Embed(
            title="📋 내 보험 정보",
            description=f"{interaction.user.display_name}님의 보험 현황입니다.",
            color=discord.Color.green()
        )
        embed.add_field(name="보험 종류", value=insurance_info["type"].capitalize(), inline=False)
        embed.add_field(name="가입 상태", value="가입중", inline=False)
        embed.add_field(name="만료일", value=expiry_date.strftime('%Y년 %m월 %d일 %H시 %M분'), inline=False)
        embed.add_field(name="최대 보상 금액", value=f"{self.INSURANCE_BENEFITS.get(insurance_info['type'], 0)}원",
                        inline=False)
        embed.set_footer(text="보험 관련 문의는 관리자에게 해주세요.")

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="보험청구", description="보험금을 청구합니다.")
    @app_commands.describe(사고내용="사고 발생 내용 (상세히)", 청구금액="청구할 금액")
    @app_commands.guild_only()
    async def claim_insurance(self, interaction: discord.Interaction, 사고내용: str, 청구금액: app_commands.Range[int, 1]):
        await interaction.response.defer(ephemeral=True)

        server_config = self.get_server_config(interaction.guild.id)
        if not server_config:
            await interaction.followup.send(
                "❌ 이 서버의 봇 설정이 완료되지 않았습니다. 관리자에게 문의하여 `/설정` 명령어를 사용해 필요한 채널과 역할을 설정해달라고 요청하세요.", ephemeral=True)
            return

        insurance_admin_role_id = server_config.get('insurance_admin_role_id')
        insurance_notification_channel_id = server_config.get('insurance_notification_channel_id')

        if not all([insurance_admin_role_id, insurance_notification_channel_id]):
            await interaction.followup.send(
                "❌ 보험 봇의 필수 설정(보험 관리 역할, 보험 알림 채널)이 완료되지 않았습니다. "
                "관리자에게 문의하여 `/설정` 명령어를 사용해 필요한 채널과 역할을 설정해달라고 요청하세요.", ephemeral=True)
            return

        conn = self.get_db_connection()
        cursor = conn.cursor()
        user_id = str(interaction.user.id)
        cursor.execute("SELECT type, status, expiry_date FROM insurance_policies WHERE user_id = ?", (user_id,))
        insurance_info = cursor.fetchone()

        if not insurance_info or insurance_info["status"] != "가입중" or datetime.datetime.fromisoformat(
                insurance_info["expiry_date"]) < datetime.datetime.utcnow():
            conn.close()
            await interaction.followup.send("❌ 현재 가입된 보험이 없거나 만료되었습니다! 보험 가입 후 다시 시도해주세요.", ephemeral=True)
            return

        insurance_type = insurance_info["type"]
        max_benefit = self.INSURANCE_BENEFITS.get(insurance_type, 0)

        if 청구금액 > max_benefit:
            conn.close()
            await interaction.followup.send(f"❌ 청구 금액이 가입된 {insurance_type}의 최대 보상 금액({max_benefit}원)을 초과할 수 없습니다!",
                                            ephemeral=True)
            return

        cursor.execute("""
                       INSERT INTO insurance_claims (user_id, username, type, description, amount, status, timestamp,
                                                     guild_id, channel_id)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                       """, (user_id, interaction.user.display_name, insurance_type, 사고내용, 청구금액, "검토중",
                             datetime.datetime.utcnow().isoformat(), str(interaction.guild.id),
                             str(interaction.channel.id)))
        claim_id = cursor.lastrowid
        conn.commit()
        conn.close()

        claim_embed = discord.Embed(
            title=f"🚨 보험금 청구 접수: #{claim_id}",
            description=f"{interaction.user.display_name}님이 보험금을 청구했습니다.",
            color=discord.Color.red()
        )
        claim_embed.add_field(name="보험 종류", value=insurance_type.capitalize(), inline=False)
        claim_embed.add_field(name="사고 내용", value=사고내용, inline=False)
        claim_embed.add_field(name="청구 금액", value=f"{청구금액}원", inline=False)
        claim_embed.add_field(name="처리 상태", value="검토중", inline=False)
        claim_embed.set_footer(
            text=f"청구 시간: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} | 서버 ID: {interaction.guild.id}")

        admin_channel = self.bot.get_channel(int(insurance_notification_channel_id))
        if admin_channel:
            admin_role = interaction.guild.get_role(int(insurance_admin_role_id))
            admin_mention = admin_role.mention if admin_role else "@관리자"
            await admin_channel.send(
                f"{admin_mention} **새로운 보험금 청구 요청이 있습니다!** (ID: `{claim_id}`)",
                embed=claim_embed
            )
        else:
            await interaction.followup.send("❌ 서버에 설정된 '보험 알림 채널'을 찾을 수 없습니다. 관리자에게 문의하세요.", ephemeral=True)
            return

        await interaction.followup.send(
            f"✅ 보험금 청구 (ID: **#{claim_id}**)가 접수되었습니다. 관리자 확인 후 처리됩니다!",
            ephemeral=True
        )

    @app_commands.command(name="청구처리", description="보험금 청구를 승인하거나 거부합니다.")
    @app_commands.describe(청구ID="처리할 청구의 ID", 처리결과="승인 또는 거부", 사유="처리 사유 (거부 시 필수)")
    @app_commands.guild_only()
    async def process_claim(self, interaction: discord.Interaction, 청구ID: int, 처리결과: str, 사유: str = "사유 없음"):
        await interaction.response.defer(ephemeral=True)

        server_config = self.get_server_config(interaction.guild.id)
        if not server_config or not server_config.get('insurance_admin_role_id'):
            await interaction.followup.send("❌ 이 서버의 보험 봇 설정이 완료되지 않았거나, 보험 관리 역할이 설정되지 않았습니다.", ephemeral=True)
            return

        required_role_id = int(server_config['insurance_admin_role_id'])
        if not any(role.id == required_role_id for role in interaction.user.roles):
            await interaction.followup.send(
                f"❌ 이 명령어를 사용할 권한이 없습니다. '{interaction.guild.get_role(required_role_id).name if interaction.guild.get_role(required_role_id) else '설정된 관리자 역할'}'이 필요합니다.",
                ephemeral=True)
            return

        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM insurance_claims WHERE id = ?", (청구ID,))
        claim = cursor.fetchone()

        if not claim:
            conn.close()
            await interaction.followup.send("❌ 유효하지 않은 청구 ID입니다!", ephemeral=True)
            return

        claim_user = await self.bot.fetch_user(claim["user_id"])
        normalized_result = 처리결과.strip().lower()

        if normalized_result not in ["승인", "거부"]:
            conn.close()
            await interaction.followup.send("❌ 처리 결과는 '승인' 또는 '거부'여야 합니다!", ephemeral=True)
            return

        if normalized_result == "거부" and 사유 == "사유 없음":
            conn.close()
            await interaction.followup.send("❌ 거부 시에는 반드시 사유를 입력해주세요!", ephemeral=True)
            return

        if claim["status"] != "검토중":
            conn.close()
            await interaction.followup.send(f"❌ 이미 처리된 청구입니다! (현재 상태: {claim['status']})", ephemeral=True)
            return

        update_status = ""
        if normalized_result == "승인":
            update_status = "지급완료"
        elif normalized_result == "거부":
            update_status = "거부됨"

        cursor.execute("""
                       UPDATE insurance_claims
                       SET status            = ?,
                           processed_by      = ?,
                           processed_by_name = ?,
                           processed_at      = ?,
                           process_reason    = ?
                       WHERE id = ?
                       """, (update_status, str(interaction.user.id), interaction.user.display_name,
                             datetime.datetime.utcnow().isoformat(), 사유, 청구ID))
        conn.commit()
        conn.close()

        if normalized_result == "승인":
            if claim_user:
                try:
                    await claim_user.send(
                        f"✅ 보험금 청구 (ID: **#{claim_id}**)가 **승인**되어 **{claim['amount']}원**이 지급되었습니다!\n"
                        f"사유: {사유 if 사유 != '사유 없음' else '없음'}"
                    )
                except discord.Forbidden:
                    print(f"유저 {claim_user.display_name}에게 DM을 보낼 수 없습니다.")
            await interaction.followup.send(
                f"✅ 청구 ID **#{claim_id}**가 **승인**되어 {claim['amount']}원이 지급되었습니다."
            )
        elif normalized_result == "거부":
            if claim_user:
                try:
                    await claim_user.send(
                        f"❌ 보험금 청구 (ID: **#{claim_id}**)가 **거부**되었습니다.\n"
                        f"사유: {사유}"
                    )
                except discord.Forbidden:
                    print(f"유저 {claim_user.display_name}에게 DM을 보낼 수 없습니다.")
            await interaction.followup.send(
                f"❌ 청구 ID **#{claim_id}**가 **거부**되었습니다. 사유: {사유}"
            )


async def setup(bot):
    await bot.add_cog(Insurance(bot))