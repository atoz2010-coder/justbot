import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import datetime


class Car(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.get_db_connection = bot.get_db_connection
        self.get_server_config = bot.get_server_config

    FORBIDDEN_CARS = ["탱크", "전투기", "핵잠수함", "우주선"]
    CAR_REGISTRATION_TAX = 50000

    class ApprovalButtons(discord.ui.View):
        def __init__(self, bot_instance, user_id: int, car_name: str, original_interaction_user_mention: str,
                     interaction_id: int, guild_id: int):
            super().__init__(timeout=300)
            self.bot_instance = bot_instance
            self.user_id = user_id
            self.car_name = car_name
            self.original_interaction_user_mention = original_interaction_user_mention
            self.interaction_id = interaction_id
            self.guild_id = guild_id

        @discord.ui.button(label="승인 ✅", style=discord.ButtonStyle.success, custom_id="approve_car")
        async def approve_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
            for item in self.children:
                item.disabled = True
            await interaction.response.edit_message(view=self)

            approved_user = await self.bot_instance.fetch_user(self.user_id)
            if approved_user:
                conn = self.bot_instance.get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                               UPDATE car_registrations
                               SET status      = ?,
                                   approved_by = ?,
                                   approved_at = ?
                               WHERE id = ?
                               """, ("승인됨", str(interaction.user.id), datetime.datetime.utcnow().isoformat(),
                                     self.interaction_id))
                conn.commit()
                conn.close()

                registration_certificate_embed = discord.Embed(
                    title=f"🚗 {self.car_name} 차량 등록증",
                    description=f"{approved_user.mention}님의 차량이 성공적으로 등록되었습니다!",
                    color=discord.Color.blue()
                )
                registration_certificate_embed.add_field(name="차량 이름", value=self.car_name, inline=False)
                registration_certificate_embed.add_field(name="등록세", value=f"{Car.CAR_REGISTRATION_TAX}원 (납부 완료)",
                                                         inline=False)
                registration_certificate_embed.set_footer(text=f"승인 관리자: {interaction.user.display_name}")
                registration_certificate_embed.set_thumbnail(
                    url=approved_user.avatar.url if approved_user.avatar else None)

                server_config = self.bot_instance.get_server_config(self.guild_id)
                if server_config and server_config['approved_cars_channel_id']:
                    approved_channel = self.bot_instance.get_channel(int(server_config['approved_cars_channel_id']))
                    if approved_channel:
                        await approved_channel.send(f"{self.original_interaction_user_mention}님, 차량 등록이 승인되었습니다!",
                                                    embed=registration_certificate_embed)
                        await interaction.followup.send(f"✅ {self.car_name} 차량이 승인되어 등록증이 발급되었습니다.", ephemeral=False)
                    else:
                        await interaction.followup.send("❌ 서버에 설정된 '차량 승인 채널'을 찾을 수 없습니다. 관리자에게 문의하세요.", ephemeral=True)
                else:
                    await interaction.followup.send("❌ 서버에 '차량 승인 채널'이 설정되어 있지 않습니다. 관리자에게 문의하세요.", ephemeral=True)
            else:
                await interaction.followup.send("원래 신청자를 찾을 수 없어 차량 등록증을 발급할 수 없습니다.", ephemeral=True)
            self.stop()

        @discord.ui.button(label="거부 ❌", style=discord.ButtonStyle.danger, custom_id="reject_car")
        async def reject_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
            for item in self.children:
                item.disabled = True
            await interaction.response.edit_message(view=self)

            class RejectModal(discord.ui.Modal, title="차량 등록 거부 사유 입력"):
                reason = discord.ui.TextInput(label="거부 사유", style=discord.TextStyle.paragraph, required=True,
                                              placeholder="예: 금지 차량, 정보 부족 등")

                async def on_submit(self, modal_interaction: discord.Interaction):
                    rejected_user = await self.bot_instance.fetch_user(self.user_id)
                    conn = self.bot_instance.get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                                   UPDATE car_registrations
                                   SET status           = ?,
                                       rejected_by      = ?,
                                       rejected_at      = ?,
                                       rejection_reason = ?
                                   WHERE id = ?
                                   """, ("거부됨", str(modal_interaction.user.id), datetime.datetime.utcnow().isoformat(),
                                         self.reason.value, self.interaction_id))
                    conn.commit()
                    conn.close()

                    if rejected_user:
                        await rejected_user.send(
                            f"❌ {self.car_name} 차량 등록 신청이 거부되었습니다.\n"
                            f"**사유:** {self.reason.value}\n"
                            f"궁금한 점이 있다면 관리자에게 문의해주세요."
                        )
                        await modal_interaction.response.send_message(
                            f"❌ {self.car_name} 차량 등록이 거부되었고, 신청자에게 사유가 전달되었습니다.", ephemeral=False)
                    else:
                        await modal_interaction.response.send_message(
                            "원래 신청자를 찾을 수 없어 거부 메시지를 보낼 수 없습니다.", ephemeral=True)
                    self.stop()

            await interaction.response.send_modal(RejectModal())
            self.stop()

        async def on_timeout(self):
            for item in self.children:
                item.disabled = True
            if self.message:
                await self.message.edit(view=self)
            conn = self.bot_instance.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                           UPDATE car_registrations
                           SET status       = ?,
                               timed_out_at = ?
                           WHERE id = ?
                           """, ("검토 시간 초과", datetime.datetime.utcnow().isoformat(), self.interaction_id))
            conn.commit()
            conn.close()
            print("버튼 타임아웃!")

    @app_commands.command(name="차량등록", description="새 차량을 RP 서버에 등록합니다.")
    @app_commands.describe(
        차량이름="등록할 차량의 이름 (예: 람보르기니 아벤타도르)"
    )
    async def register_car(self, interaction: discord.Interaction, 차량이름: str):
        await interaction.response.defer(ephemeral=True)

        if not interaction.guild:
            await interaction.followup.send("❌ 이 명령어는 서버(길드)에서만 사용할 수 있습니다.", ephemeral=True)
            return

        server_config = self.get_server_config(interaction.guild.id)
        if not server_config:
            await interaction.followup.send(
                "❌ 이 서버의 봇 설정이 완료되지 않았습니다. 관리자에게 문의하여 `/설정` 명령어를 사용해 필요한 채널과 역할을 설정해달라고 요청하세요.", ephemeral=True)
            return

        registration_channel_id = server_config.get('registration_channel_id')
        car_admin_channel_id = server_config.get('car_admin_channel_id')
        car_admin_role_id = server_config.get('car_admin_role_id')
        approved_cars_channel_id = server_config.get('approved_cars_channel_id')

        if not all([registration_channel_id, car_admin_channel_id, car_admin_role_id, approved_cars_channel_id]):
            await interaction.followup.send(
                "❌ 차량 관리 봇의 필수 설정(차량 등록 채널, 관리 채널, 관리 역할, 승인 채널)이 완료되지 않았습니다. "
                "관리자에게 문의하여 `/설정` 명령어를 사용해 필요한 채널과 역할을 설정해달라고 요청하세요.", ephemeral=True)
            return

        if 차량이름.lower() in [c.lower() for c in self.FORBIDDEN_CARS]:
            await interaction.followup.send(f"🚫 '{차량이름}'은(는) RP 서버에 등록할 수 없는 **금지 차량**입니다.", ephemeral=True)
            return

        conn = self.get_db_connection()
        cursor = conn.cursor()
        user_id = str(interaction.user.id)

        cursor.execute("SELECT balance FROM bank_accounts WHERE user_id = ?", (user_id,))
        bank_account = cursor.fetchone()
        current_balance = bank_account["balance"] if bank_account else 0

        if current_balance < self.CAR_REGISTRATION_TAX:
            conn.close()
            await interaction.followup.send(
                f"❌ 잔고가 부족합니다! 차량 등록세 **{self.CAR_REGISTRATION_TAX}원**이 필요합니다. 현재 잔고: {current_balance}원",
                ephemeral=True)
            return

        try:
            cursor.execute("UPDATE bank_accounts SET balance = balance - ? WHERE user_id = ?",
                           (self.CAR_REGISTRATION_TAX, user_id))

            car_doc = {
                "user_id": user_id,
                "username": interaction.user.display_name,
                "car_name": 차량이름,
                "registration_tax": self.CAR_REGISTRATION_TAX,
                "status": "검토중",
                "requested_at": datetime.datetime.utcnow().isoformat(),
                "guild_id": str(interaction.guild.id),
                "channel_id": str(interaction.channel.id)
            }
            cursor.execute("""
                           INSERT INTO car_registrations (user_id, username, car_name, registration_tax, status,
                                                          requested_at, guild_id, channel_id)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                           """,
                           (car_doc["user_id"], car_doc["username"], car_doc["car_name"], car_doc["registration_tax"],
                            car_doc["status"], car_doc["requested_at"], car_doc["guild_id"], car_doc["channel_id"]))
            doc_id = cursor.lastrowid

            conn.commit()
        except Exception as e:
            conn.rollback()
            conn.close()
            print(f"차량 등록 및 결제 중 오류 발생: {e}")
            await interaction.followup.send("❌ 차량 등록 및 결제 처리 중 오류가 발생했습니다. 관리자에게 문의하세요.", ephemeral=True)
            return
        finally:
            conn.close()

        registration_embed = discord.Embed(
            title=f"🚗 신규 차량 등록 신청: {차량이름}",
            description=f"**신청자:** {interaction.user.mention} ({interaction.user.display_name})",
            color=discord.Color.gold()
        )
        registration_embed.add_field(name="차량 이름", value=차량이름, inline=False)
        registration_embed.add_field(name="등록세", value=f"**{self.CAR_REGISTRATION_TAX}원**", inline=False)
        registration_embed.set_footer(text=f"신청 ID: {doc_id} | 서버 ID: {interaction.guild.id}")
        registration_embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else None)

        registration_channel = self.bot.get_channel(int(registration_channel_id))
        if registration_channel:
            await registration_channel.send(
                f"**차량 등록 신청 완료!** (신청자: {interaction.user.display_name})",
                embed=registration_embed
            )
        else:
            await interaction.followup.send("❌ 서버에 설정된 '차량 등록 채널'을 찾을 수 없습니다. 관리자에게 문의하세요.", ephemeral=True)
            return

        admin_channel = self.bot.get_channel(int(car_admin_channel_id))
        if admin_channel:
            admin_notification_embed = discord.Embed(
                title="🚨 차량 등록 신청 검토 요청",
                description=f"{interaction.user.mention}님이 새 차량 등록을 신청했습니다. 검토해주세요!",
                color=discord.Color.red()
            )
            admin_notification_embed.add_field(name="신청자", value=interaction.user.display_name, inline=True)
            admin_notification_embed.add_field(name="차량 이름", value=차량이름, inline=True)
            admin_notification_embed.add_field(name="등록세", value=f"**{self.CAR_REGISTRATION_TAX}원**", inline=True)
            admin_notification_embed.set_footer(text=f"신청 ID: {doc_id} | 서버 ID: {interaction.guild.id}")

            view = self.ApprovalButtons(
                self.bot,
                user_id=interaction.user.id,
                car_name=차량이름,
                original_interaction_user_mention=interaction.user.mention,
                interaction_id=doc_id,
                guild_id=interaction.guild.id
            )

            try:
                admin_role = interaction.guild.get_role(int(car_admin_role_id))
                if admin_role:
                    message = await admin_channel.send(
                        f"{admin_role.mention} **차량 등록 신청이 들어왔습니다!**",
                        embed=admin_notification_embed,
                        view=view
                    )
                    view.message = message
                else:
                    await interaction.followup.send(
                        "서버에 설정된 '차량 관리 역할'을 찾을 수 없습니다. 관리자에게 문의하세요.",
                        ephemeral=True
                    )
                    return
            except Exception as e:
                print(f"관리자 채널 메시지 전송 실패: {e}")
                await interaction.followup.send("❌ 관리자 채널에 알림을 보내는 데 실패했습니다. 봇 설정 확인 필요!", ephemeral=True)
                return

            await interaction.followup.send(
                f"✅ **{차량이름}** 차량 등록 신청이 완료되었습니다! 은행 계좌에서 **등록세 {self.CAR_REGISTRATION_TAX}원**이 차감되었습니다. 관리자 확인 후 처리됩니다. 기다려 주세요!",
                ephemeral=True
            )
        else:
            await interaction.followup.send("❌ 서버에 설정된 '차량 관리 채널'을 찾을 수 없습니다. 관리자에게 문의하세요.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Car(bot))