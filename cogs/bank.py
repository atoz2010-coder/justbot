import discord
from discord.ext import commands
from discord import app_commands
import datetime
import sqlite3


class Bank(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.get_db_connection = bot.get_db_connection

    @app_commands.command(name="잔액", description="현재 잔액을 확인합니다.")
    async def balance(self, interaction: discord.Interaction):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        user_id = str(interaction.user.id)
        cursor.execute("SELECT balance FROM bank_accounts WHERE user_id = ?", (user_id,))
        account = cursor.fetchone()
        conn.close()
        balance = account["balance"] if account else 0
        await interaction.response.send_message(f"🏦 {interaction.user.display_name}님의 현재 잔액은 **{balance}원**입니다.",
                                                ephemeral=True)

    @app_commands.command(name="입금", description="자신에게 돈을 입금합니다.")
    @app_commands.describe(금액="입금할 금액")
    async def deposit(self, interaction: discord.Interaction, 금액: int):
        if 금액 <= 0:
            await interaction.response.send_message("❌ 0원 이하의 금액은 입금할 수 없습니다!", ephemeral=True)
            return

        conn = self.get_db_connection()
        cursor = conn.cursor()
        user_id = str(interaction.user.id)
        username = interaction.user.display_name

        cursor.execute(
            "INSERT INTO bank_accounts (user_id, username, balance) VALUES (?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET balance = balance + ?",
            (user_id, username, 금액, 금액))
        conn.commit()

        cursor.execute("SELECT balance FROM bank_accounts WHERE user_id = ?", (user_id,))
        account = cursor.fetchone()
        conn.close()
        await interaction.response.send_message(f"💰 {금액}원이 입금되었습니다. 현재 잔액: **{account['balance']}원**", ephemeral=True)

    @app_commands.command(name="출금", description="자신에게서 돈을 출금합니다.")
    @app_commands.describe(금액="출금할 금액")
    async def withdraw(self, interaction: discord.Interaction, 금액: int):
        if 금액 <= 0:
            await interaction.response.send_message("❌ 0원 이하의 금액은 출금할 수 없습니다!", ephemeral=True)
            return

        conn = self.get_db_connection()
        cursor = conn.cursor()
        user_id = str(interaction.user.id)

        cursor.execute("SELECT balance FROM bank_accounts WHERE user_id = ?", (user_id,))
        account = cursor.fetchone()
        current_balance = account["balance"] if account else 0

        if current_balance < 금액:
            conn.close()
            await interaction.response.send_message("💸 잔액이 부족합니다!", ephemeral=True)
            return

        cursor.execute("UPDATE bank_accounts SET balance = balance - ? WHERE user_id = ?", (금액, user_id))
        conn.commit()

        cursor.execute("SELECT balance FROM bank_accounts WHERE user_id = ?", (user_id,))
        account = cursor.fetchone()
        conn.close()
        await interaction.response.send_message(f"💸 {금액}원이 출금되었습니다. 현재 잔액: **{account['balance']}원**", ephemeral=True)

    @app_commands.command(name="송금", description="다른 유저에게 돈을 송금합니다.")
    @app_commands.describe(수신자="돈을 보낼 유저", 금액="송금할 금액")
    @app_commands.guild_only()
    async def transfer(self, interaction: discord.Interaction, 수신자: discord.Member, 금액: int):
        if 금액 <= 0:
            await interaction.response.send_message("❌ 0원 이하의 금액은 송금할 수 없습니다!", ephemeral=True)
            return
        if 수신자.bot:
            await interaction.response.send_message("❌ 봇에게는 송금할 수 없습니다!", ephemeral=True)
            return
        if 수신자.id == interaction.user.id:
            await interaction.response.send_message("❌ 자기 자신에게는 송금할 수 없습니다!", ephemeral=True)
            return

        conn = self.get_db_connection()
        cursor = conn.cursor()
        sender_id = str(interaction.user.id)
        receiver_id = str(수신자.id)

        cursor.execute("SELECT balance FROM bank_accounts WHERE user_id = ?", (sender_id,))
        sender_account = cursor.fetchone()
        sender_balance = sender_account["balance"] if sender_account else 0

        if sender_balance < 금액:
            conn.close()
            await interaction.response.send_message("💸 잔액이 부족해서 송금할 수 없습니다!", ephemeral=True)
            return

        cursor.execute("UPDATE bank_accounts SET balance = balance - ? WHERE user_id = ?", (금액, sender_id))
        cursor.execute(
            "INSERT INTO bank_accounts (user_id, username, balance) VALUES (?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET balance = balance + ?",
            (receiver_id, 수신자.display_name, 금액, 금액))
        conn.commit()

        cursor.execute("SELECT balance FROM bank_accounts WHERE user_id = ?", (sender_id,))
        updated_sender_account = cursor.fetchone()
        cursor.execute("SELECT balance FROM bank_accounts WHERE user_id = ?", (receiver_id,))
        updated_receiver_account = cursor.fetchone()
        conn.close()

        await interaction.response.send_message(
            f"✅ {수신자.display_name}님에게 **{금액}원**을 송금했습니다. "
            f"내 잔액: **{updated_sender_account['balance']}원**", ephemeral=True)

        try:
            await 수신자.send(
                f"💰 {interaction.user.display_name}님으로부터 **{금액}원**을 송금받았습니다. 현재 잔액: **{updated_receiver_account['balance']}원**")
        except discord.Forbidden:
            print(f"수신자 {수신자.display_name}에게 DM을 보낼 수 없습니다.")


async def setup(bot):
    await bot.add_cog(Bank(bot))