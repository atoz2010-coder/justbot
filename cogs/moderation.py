import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import datetime


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 메인 bot에서 주입된 함수들
        self.get_db_connection = bot.get_db_connection
        self.get_server_config = bot.get_server_config
        self.set_server_config = bot.set_server_config

    # --- 서버별 설정 명령어 그룹 ---
    config_group = app_commands.Group(name="설정", description="이 서버의 봇 설정을 관리합니다.", guild_only=True)

    @config_group.command(name="차량등록채널", description="차량 등록 신청 포스트가 올라올 채널을 설정합니다.")
    @app_commands.describe(채널="설정할 채널")
    @commands.has_permissions(administrator=True)
    async def set_registration_channel(self, interaction: discord.Interaction, 채널: discord.TextChannel):
        self.set_server_config(interaction.guild.id, 'registration_channel_id', 채널.id)
        await interaction.response.send_message(f"✅ 차량 등록 채널이 {채널.mention}으로 설정되었습니다.", ephemeral=True)

    @config_group.command(name="차량관리채널", description="차량 등록 알림 및 관리 버튼이 표시될 채널을 설정합니다.")
    @app_commands.describe(채널="설정할 채널")
    @commands.has_permissions(administrator=True)
    async def set_car_admin_channel(self, interaction: discord.Interaction, 채널: discord.TextChannel):
        self.set_server_config(interaction.guild.id, 'car_admin_channel_id', 채널.id)
        await interaction.response.send_message(f"✅ 차량 관리 채널이 {채널.mention}으로 설정되었습니다.", ephemeral=True)

    @config_group.command(name="차량관리역할", description="차량 등록 알림 멘션을 받을 관리자 역할을 설정합니다.")
    @app_commands.describe(역할="설정할 역할")
    @commands.has_permissions(administrator=True)
    async def set_car_admin_role(self, interaction: discord.Interaction, 역할: discord.Role):
        self.set_server_config(interaction.guild.id, 'car_admin_role_id', 역할.id)
        await interaction.response.send_message(f"✅ 차량 관리 역할이 {역할.mention}으로 설정되었습니다.", ephemeral=True)

    @config_group.command(name="차량승인채널", description="승인된 차량 등록증이 올라올 채널을 설정합니다.")
    @app_commands.describe(채널="설정할 채널")
    @commands.has_permissions(administrator=True)
    async def set_approved_cars_channel(self, interaction: discord.Interaction, 채널: discord.TextChannel):
        self.set_server_config(interaction.guild.id, 'approved_cars_channel_id', 채널.id)
        await interaction.response.send_message(f"✅ 차량 승인 채널이 {채널.mention}으로 설정되었습니다.", ephemeral=True)

    @config_group.command(name="보험관리역할", description="보험 청구 알림 멘션을 받을 관리자 역할을 설정합니다.")
    @app_commands.describe(역할="설정할 역할")
    @commands.has_permissions(administrator=True)
    async def set_insurance_admin_role(self, interaction: discord.Interaction, 역할: discord.Role):
        self.set_server_config(interaction.guild.id, 'insurance_admin_role_id', 역할.id)
        await interaction.response.send_message(f"✅ 보험 관리 역할이 {역할.mention}으로 설정되었습니다.", ephemeral=True)

    @config_group.command(name="보험알림채널", description="새로운 보험 청구 알림이 표시될 채널을 설정합니다.")
    @app_commands.describe(채널="설정할 채널")
    @commands.has_permissions(administrator=True)
    async def set_insurance_notification_channel(self, interaction: discord.Interaction, 채널: discord.TextChannel):
        self.set_server_config(interaction.guild.id, 'insurance_notification_channel_id', 채널.id)
        await interaction.response.send_message(f"✅ 보험 알림 채널이 {채널.mention}으로 설정되었습니다.", ephemeral=True)

    @config_group.command(name="티켓개설채널", description="사용자가 /ticket open을 사용할 수 있는 채널을 설정합니다.")
    @app_commands.describe(채널="설정할 채널")
    @commands.has_permissions(administrator=True)
    async def set_ticket_open_channel(self, interaction: discord.Interaction, 채널: discord.TextChannel):
        self.set_server_config(interaction.guild.id, 'ticket_open_channel_id', 채널.id)
        await interaction.response.send_message(f"✅ 티켓 개설 채널이 {채널.mention}으로 설정되었습니다.", ephemeral=True)

    @config_group.command(name="티켓카테고리", description="새 티켓 채널이 생성될 카테고리를 설정합니다.")
    @app_commands.describe(카테고리="설정할 카테고리")
    @commands.has_permissions(administrator=True)
    async def set_ticket_category(self, interaction: discord.Interaction, 카테고리: discord.CategoryChannel):
        self.set_server_config(interaction.guild.id, 'ticket_category_id', 카테고리.id)
        await interaction.response.send_message(f"✅ 티켓 카테고리가 '{카테고리.name}'으로 설정되었습니다.", ephemeral=True)

    @config_group.command(name="티켓관리역할", description="티켓 채널에 자동 추가될 스태프 역할을 설정합니다.")
    @app_commands.describe(역할="설정할 역할")
    @commands.has_permissions(administrator=True)
    async def set_ticket_staff_role(self, interaction: discord.Interaction, 역할: discord.Role):
        self.set_server_config(interaction.guild.id, 'ticket_staff_role_id', 역할.id)
        await interaction.response.send_message(f"✅ 티켓 스태프 역할이 {역할.mention}으로 설정되었습니다.", ephemeral=True)

    @config_group.command(name="모든설정확인", description="이 서버의 현재 봇 설정들을 확인합니다.")
    @commands.has_permissions(administrator=True)
    async def show_all_configs(self, interaction: discord.Interaction):
        server_config = self.get_server_config(interaction.guild.id)
        if not server_config:
            await interaction.response.send_message("❌ 이 서버에 저장된 봇 설정이 없습니다. `/설정` 명령어를 사용해 설정해주세요.", ephemeral=True)
            return

        config_details = "--- 현재 서버 설정 ---\n"
        for key, value in server_config.items():
            if key == 'guild_id':
                config_details += f"**서버 ID:** {value}\n"
            elif '_channel_id' in key and value:
                channel = self.bot.get_channel(int(value))
                config_details += f"**{key.replace('_id', '').replace('_channel', ' 채널')}:** {channel.mention if channel else '채널을 찾을 수 없음'} (`{value}`)\n"
            elif '_role_id' in key and value:
                role = interaction.guild.get_role(int(value))
                config_details += f"**{key.replace('_id', '').replace('_role', ' 역할')}:** {role.mention if role else '역할을 찾을 수 없음'} (`{value}`)\n"
            elif '_category_id' in key and value:
                category = self.bot.get_channel(int(value))
                config_details += f"**{key.replace('_id', '').replace('_category', ' 카테고리')}:** {category.name if category else '카테고리를 찾을 수 없음'} (`{value}`)\n"
            else:
                config_details += f"**{key}:** {value}\n"

        embed = discord.Embed(
            title=f"{interaction.guild.name} 서버의 봇 설정",
            description=config_details,
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ 이 명령어를 사용할 권한이 없습니다. 관리자(Administrator) 권한이 필요합니다.",
                                                    ephemeral=True)
        else:
            print(f"오류 발생: {error}")
            await interaction.response.send_message(f"오류가 발생했습니다: {error}", ephemeral=True)

    @app_commands.command(name="킥", description="유저를 서버에서 강퇴시킵니다.")
    @app_commands.describe(유저="강퇴할 유저", 사유="강퇴 사유")
    @commands.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, 유저: discord.Member, 사유: str = "사유 없음"):
        if 유저.id == interaction.user.id:
            await interaction.response.send_message("❌ 자기 자신을 킥할 순 없습니다!", ephemeral=True)
            return
        if 유저.top_role >= interaction.user.top_role and 유저.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ 당신보다 높은 역할의 유저는 킥할 수 없습니다!", ephemeral=True)
            return
        if 유저.id == interaction.guild.owner_id:
            await interaction.response.send_message("❌ 서버장은 킥할 수 없습니다!", ephemeral=True)
            return
        try:
            await 유저.kick(reason=사유)
            await interaction.response.send_message(f"✅ {유저.display_name}님을 강퇴했습니다. 사유: {사유}")
            await 유저.send(f"🚨 당신은 {interaction.guild.name} 서버에서 강퇴당했습니다. 사유: {사유}")
        except discord.Forbidden:
            await interaction.response.send_message("❌ 봇에게 강퇴 권한이 없거나, 대상 유저의 역할이 봇보다 높습니다.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ 킥 실패: {e}", ephemeral=True)

    @app_commands.command(name="밴", description="유저를 서버에서 추방시킵니다.")
    @app_commands.describe(유저="추방할 유저", 사유="추방 사유", 일수="메시지 삭제 일수 (최대 7일)")
    @commands.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, 유저: discord.Member, 사유: str = "사유 없음",
                  일수: app_commands.Range[int, 0, 7] = 0):
        if 유저.id == interaction.user.id:
            await interaction.response.send_message("❌ 자기 자신을 밴할 순 없습니다!", ephemeral=True)
            return
        if 유저.top_role >= interaction.user.top_role and 유저.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ 당신보다 높은 역할의 유저는 밴할 수 없습니다!", ephemeral=True)
            return
        if 유저.id == interaction.guild.owner_id:
            await interaction.response.send_message("❌ 서버장은 밴할 수 없습니다!", ephemeral=True)
            return
        try:
            await 유저.ban(reason=사유, delete_message_days=일수)
            await interaction.response.send_message(f"✅ {유저.display_name}님을 추방했습니다. 사유: {사유}, 메시지 삭제 일수: {일수}일")
            await 유저.send(f"🚨 당신은 {interaction.guild.name} 서버에서 추방당했습니다. 사유: {사유}")
        except discord.Forbidden:
            await interaction.response.send_message("❌ 봇에게 추방 권한이 없거나, 대상 유저의 역할이 봇보다 높습니다.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ 밴 실패: {e}", ephemeral=True)

    @app_commands.command(name="청소", description="채널의 메시지를 삭제합니다.")
    @app_commands.describe(개수="삭제할 메시지 개수 (최대 100개)")
    @commands.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, 개수: app_commands.Range[int, 1, 100]):
        try:
            await interaction.response.defer(ephemeral=True)
            deleted = await interaction.channel.purge(limit=개수)
            await interaction.followup.send(f"✅ 메시지 {len(deleted)}개를 삭제했습니다.", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("❌ 봇에게 메시지 관리 권한이 없습니다.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ 청소 실패: {e}", ephemeral=True)

    @app_commands.command(name="역할부여", description="유저에게 역할을 부여합니다.")
    @app_commands.describe(유저="역할을 부여할 유저", 역할="부여할 역할")
    @commands.has_permissions(manage_roles=True)
    async def add_role(self, interaction: discord.Interaction, 유저: discord.Member, 역할: discord.Role):
        if 역할 >= interaction.guild.me.top_role:
            await interaction.response.send_message("❌ 봇보다 높은 역할은 부여할 수 없습니다!", ephemeral=True)
            return
        if 역할 >= interaction.user.top_role:
            await interaction.response.send_message("❌ 당신보다 높은 역할은 부여할 수 없습니다!", ephemeral=True)
            return
        try:
            await 유저.add_roles(역할)
            await interaction.response.send_message(f"✅ {유저.display_name}님에게 '{역할.name}' 역할을 부여했습니다.")
        except discord.Forbidden:
            await interaction.response.send_message("❌ 봇에게 역할 관리 권한이 없거나, 대상 역할의 위치가 봇보다 높습니다.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ 역할 부여 실패: {e}", ephemeral=True)

    @app_commands.command(name="역할삭제", description="유저의 역할을 삭제합니다.")
    @app_commands.describe(유저="역할을 삭제할 유저", 역할="삭제할 역할")
    @commands.has_permissions(manage_roles=True)
    async def remove_role(self, interaction: discord.Interaction, 유저: discord.Member, 역할: discord.Role):
        if 역할 >= interaction.guild.me.top_role:
            await interaction.response.send_message("❌ 봇보다 높은 역할은 삭제할 수 없습니다!", ephemeral=True)
            return
        if 역할 >= interaction.user.top_role:
            await interaction.response.send_message("❌ 당신보다 높은 역할은 삭제할 수 없습니다!", ephemeral=True)
            return
        try:
            await 유저.remove_roles(역할)
            await interaction.response.send_message(f"✅ {유저.display_name}님에게서 '{역할.name}' 역할을 삭제했습니다.")
        except discord.Forbidden:
            await interaction.response.send_message("❌ 봇에게 역할 관리 권한이 없거나, 대상 역할의 위치가 봇보다 높습니다.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ 역할 삭제 실패: {e}", ephemeral=True)

    @app_commands.command(name="경고", description="유저에게 경고를 부여합니다.")
    @app_commands.describe(유저="경고를 줄 유저", 사유="경고 사유")
    @commands.has_permissions(kick_members=True)
    async def warn(self, interaction: discord.Interaction, 유저: discord.Member, 사유: str = "사유 없음"):
        if 유저.bot:
            await interaction.response.send_message("❌ 봇에게는 경고를 줄 수 없습니다!", ephemeral=True)
            return
        if 유저.id == interaction.user.id:
            await interaction.response.send_message("❌ 자기 자신에게 경고를 줄 순 없습니다!", ephemeral=True)
            return
        if 유저.top_role >= interaction.user.top_role and 유저.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ 당신보다 높은 역할의 유저는 경고할 수 없습니다!", ephemeral=True)
            return

        conn = self.get_db_connection()
        cursor = conn.cursor()
        user_id_str = str(유저.id)

        cursor.execute("""
                       INSERT INTO user_warnings (user_id, username, reason, moderator_id, moderator_name, timestamp)
                       VALUES (?, ?, ?, ?, ?, ?)
                       """, (user_id_str, 유저.display_name, 사유, str(interaction.user.id), interaction.user.display_name,
                             datetime.datetime.utcnow().isoformat()))
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM user_warnings WHERE user_id = ?", (user_id_str,))
        warning_count = cursor.fetchone()[0]
        conn.close()

        warn_embed = discord.Embed(
            title="🚨 경고 알림",
            description=f"{유저.mention}님이 경고를 받았습니다.",
            color=discord.Color.red()
        )
        warn_embed.add_field(name="사유", value=사유, inline=False)
        warn_embed.add_field(name="경고 횟수", value=f"총 **{warning_count}회**", inline=False)
        warn_embed.set_footer(text=f"관리자: {interaction.user.display_name}")
        await interaction.response.send_message(embed=warn_embed)
        try:
            await 유저.send(f"🚨 {interaction.guild.name} 서버에서 경고를 받았습니다.\n사유: {사유}\n총 경고 횟수: {warning_count}회")
        except discord.Forbidden:
            print(f"유저 {유저.display_name}에게 DM을 보낼 수 없습니다.")

    @app_commands.command(name="경고조회", description="유저의 경고 내역을 조회합니다.")
    @app_commands.describe(유저="경고 내역을 조회할 유저")
    async def check_warnings(self, interaction: discord.Interaction, 유저: discord.Member):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        user_id_str = str(유저.id)
        cursor.execute(
            "SELECT reason, moderator_name, timestamp FROM user_warnings WHERE user_id = ? ORDER BY timestamp ASC",
            (user_id_str,))
        warnings = cursor.fetchall()
        conn.close()

        if not warnings:
            await interaction.response.send_message(f"✅ {유저.display_name}님은 경고 내역이 없습니다!", ephemeral=True)
            return

        warn_list_str = ""
        for i, w in enumerate(warnings):
            warn_list_str += f"{i + 1}. 사유: {w['reason']} (관리자: {w['moderator_name']}, 시간: {w['timestamp'][:10]})\n"

        embed = discord.Embed(
            title=f"⚠️ {유저.display_name}님의 경고 내역 (총 {len(warnings)}회)",
            description=warn_list_str,
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="경고삭제", description="유저의 경고를 삭제합니다.")
    @app_commands.describe(유저="경고를 삭제할 유저", 인덱스="삭제할 경고의 번호 (모두 삭제하려면 '모두')", 사유="경고 삭제 사유")
    @commands.has_permissions(kick_members=True)
    async def remove_warning(self, interaction: discord.Interaction, 유저: discord.Member, 인덱스: str, 사유: str = "사유 없음"):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        user_id_str = str(유저.id)

        if 인덱스.lower() == "모두":
            cursor.execute("DELETE FROM user_warnings WHERE user_id = ?", (user_id_str,))
            conn.commit()
            conn.close()
            await interaction.response.send_message(f"✅ {유저.display_name}님의 모든 경고를 삭제했습니다. 사유: {사유}")
        else:
            try:
                idx = int(인덱스) - 1
                cursor.execute("SELECT id FROM user_warnings WHERE user_id = ? ORDER BY timestamp ASC LIMIT 1 OFFSET ?",
                               (user_id_str, idx))
                warning_to_delete = cursor.fetchone()

                if warning_to_delete:
                    cursor.execute("DELETE FROM user_warnings WHERE id = ?", (warning_to_delete['id'],))
                    conn.commit()
                    conn.close()
                    await interaction.response.send_message(
                        f"✅ {유저.display_name}님의 {idx + 1}번째 경고를 삭제했습니다. 사유: {사유}"
                    )
                else:
                    conn.close()
                    await interaction.response.send_message("❌ 유효하지 않은 경고 번호입니다!", ephemeral=True)
            except ValueError:
                conn.close()
                await interaction.response.send_message("❌ 경고 번호는 숫자이거나 '모두'여야 합니다!", ephemeral=True)

    # --- 티켓 명령어 그룹 ---
    ticket_group = app_commands.Group(name="티켓", description="고객 지원 티켓을 관리합니다.", guild_only=True)

    @ticket_group.command(name="오픈", description="새로운 고객 지원 티켓을 엽니다.")
    @app_commands.describe(사유="티켓을 여는 이유")
    async def open_ticket(self, interaction: discord.Interaction, 사유: str = "사유 없음"):
        await interaction.response.defer(ephemeral=True)

        if not interaction.guild:
            await interaction.followup.send("❌ 이 명령어는 서버(길드)에서만 사용할 수 있습니다.", ephemeral=True)
            return

        server_config = self.get_server_config(interaction.guild.id)
        if not server_config:
            await interaction.followup.send(
                "❌ 이 서버의 봇 설정이 완료되지 않았습니다. 관리자에게 문의하여 `/설정` 명령어를 사용해 필요한 채널과 역할을 설정해달라고 요청하세요.", ephemeral=True)
            return

        ticket_open_channel_id = server_config.get('ticket_open_channel_id')
        ticket_category_id = server_config.get('ticket_category_id')
        ticket_staff_role_id = server_config.get('ticket_staff_role_id')

        if not all([ticket_open_channel_id, ticket_category_id, ticket_staff_role_id]):
            await interaction.followup.send(
                "❌ 티켓 기능의 필수 설정(티켓 개설 채널, 티켓 카테고리, 티켓 관리 역할)이 완료되지 않았습니다. "
                "관리자에게 문의하여 `/설정` 명령어를 사용해 필요한 채널과 역할을 설정해달라고 요청하세요.", ephemeral=True)
            return

        # 사용자가 올바른 채널에서 티켓을 여는지 확인
        if str(interaction.channel.id) != ticket_open_channel_id:
            ticket_channel = self.bot.get_channel(int(ticket_open_channel_id))
            await interaction.followup.send(
                f"❌ 티켓은 {ticket_channel.mention if ticket_channel else '설정된 티켓 개설 채널'}에서만 열 수 있습니다.", ephemeral=True)
            return

        # 이미 열린 티켓이 있는지 확인
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT channel_id FROM tickets WHERE user_id = ? AND status = 'open'",
                       (str(interaction.user.id),))
        if cursor.fetchone():
            conn.close()
            await interaction.followup.send("❌ 이미 열려있는 티켓이 있습니다. 먼저 기존 티켓을 닫아주세요.", ephemeral=True)
            return

        # 티켓 채널 권한 설정
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, embed_links=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, embed_links=True)
        }
        staff_role = interaction.guild.get_role(int(ticket_staff_role_id))
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True,
                                                                 embed_links=True)

        category = self.bot.get_channel(int(ticket_category_id))
        if not category or not isinstance(category, discord.CategoryChannel):
            await interaction.followup.send("❌ 설정된 티켓 카테고리를 찾을 수 없습니다. 관리자에게 문의하세요.", ephemeral=True)
            return

        try:
            ticket_channel_name = f"티켓-{interaction.user.name.lower().replace(' ', '-')}-{datetime.datetime.now().strftime('%m%d%H%M')}"
            channel = await interaction.guild.create_text_channel(
                ticket_channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"{interaction.user.name}님이 개설한 티켓입니다. 사유: {사유}"
            )

            cursor.execute("""
                           INSERT INTO tickets (user_id, username, guild_id, channel_id, status, reason, opened_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?)
                           """, (str(interaction.user.id), interaction.user.display_name, str(interaction.guild.id),
                                 str(channel.id), "open", 사유, datetime.datetime.utcnow().isoformat()))
            ticket_id = cursor.lastrowid
            conn.commit()
            conn.close()

            ticket_embed = discord.Embed(
                title=f"📝 새 티켓이 생성되었습니다! #{ticket_id}",
                description=f"{interaction.user.mention}님, 티켓을 열어주셔서 감사합니다. 스태프가 곧 연락드릴 것입니다.",
                color=discord.Color.blue()
            )
            ticket_embed.add_field(name="개설 사유", value=사유, inline=False)
            if staff_role:
                ticket_embed.set_footer(text=f"문의 사항이 있다면 {staff_role.name} 역할을 멘션해주세요.")

            await channel.send(interaction.user.mention + (staff_role.mention if staff_role else ""),
                               embed=ticket_embed)
            await interaction.followup.send(f"✅ 티켓이 성공적으로 생성되었습니다! {channel.mention}으로 이동해주세요.", ephemeral=True)

        except discord.Forbidden:
            conn.close()
            await interaction.followup.send("❌ 티켓 채널을 생성할 권한이 없습니다. 봇의 권한을 확인해주세요.", ephemeral=True)
        except Exception as e:
            conn.close()
            print(f"티켓 생성 중 오류 발생: {e}")
            await interaction.followup.send(f"❌ 티켓 생성 중 오류가 발생했습니다: {e}", ephemeral=True)

    @ticket_group.command(name="닫기", description="현재 채널의 티켓을 닫습니다.")
    @app_commands.describe(사유="티켓을 닫는 이유")
    async def close_ticket(self, interaction: discord.Interaction, 사유: str = "사유 없음"):
        await interaction.response.defer(ephemeral=True)

        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tickets WHERE channel_id = ? AND status = 'open'", (str(interaction.channel.id),))
        ticket = cursor.fetchone()

        if not ticket:
            conn.close()
            await interaction.followup.send("❌ 이 채널은 열려있는 티켓 채널이 아니거나, 이미 닫혔습니다.", ephemeral=True)
            return

        ticket_staff_role_id = self.get_server_config(interaction.guild.id).get('ticket_staff_role_id')
        is_staff = False
        if ticket_staff_role_id:
            staff_role = interaction.guild.get_role(int(ticket_staff_role_id))
            if staff_role and staff_role in interaction.user.roles:
                is_staff = True

        if str(interaction.user.id) != ticket[
            'user_id'] and not is_staff and not interaction.user.guild_permissions.administrator:
            conn.close()
            await interaction.followup.send("❌ 티켓 개설자 또는 스태프(관리자)만 티켓을 닫을 수 있습니다.", ephemeral=True)
            return

        try:
            cursor.execute("""
                           UPDATE tickets
                           SET status    = ?,
                               closed_at = ?,
                               closed_by = ?,
                               reason    = ?
                           WHERE id = ?
                           """, ("closed", datetime.datetime.utcnow().isoformat(), str(interaction.user.id), 사유,
                                 ticket['id']))
            conn.commit()
            conn.close()

            embed = discord.Embed(
                title=f"🔒 티켓 #{ticket['id']}이(가) 닫혔습니다.",
                description=f"티켓이 {interaction.user.mention}에 의해 닫혔습니다.\n**사유:** {사유}",
                color=discord.Color.red()
            )
            embed.set_footer(text="이 채널은 잠시 후 자동으로 삭제됩니다.")
            await interaction.channel.send(embed=embed)

            await interaction.followup.send(f"✅ 티켓이 성공적으로 닫혔습니다. 채널은 잠시 후 삭제됩니다.", ephemeral=True)
            await discord.utils.sleep_until(datetime.datetime.utcnow() + datetime.timedelta(seconds=5))
            await interaction.channel.delete(reason=f"티켓 #{ticket['id']} 닫힘.")

        except discord.Forbidden:
            await interaction.followup.send("❌ 채널을 삭제할 권한이 없습니다. 봇의 권한을 확인해주세요.", ephemeral=True)
        except Exception as e:
            print(f"티켓 닫기 중 오류 발생: {e}")
            await interaction.followup.send(f"❌ 티켓 닫기 중 오류가 발생했습니다: {e}", ephemeral=True)


async def setup(bot):
    bot.tree.add_command(Moderation.config_group)
    bot.tree.add_command(Moderation.ticket_group)
    await bot.add_cog(Moderation(bot))