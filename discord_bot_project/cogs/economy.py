import discord
from discord import app_commands
from discord.ext import commands
import json
import time
import os

LOG_FILE_PATH = "logs/economy_logs.txt"


# 관리자를 확인하는 함수 (관리자 role 또는 특정 사용자 ID 확인)
def is_admin(user: discord.User):
    # 여기서 관리자 ID를 설정합니다. (예: 관리자 ID를 1234567890으로 가정)
    admin_ids = [1303687103309418546]  # 관리자 사용자 ID 목록
    return user.id in admin_ids  # 이 리스트에 포함된 사용자는 관리자


def load_user_data():
    file_path = 'config/economy.json'
    if not os.path.exists(file_path):
        # 파일이 없으면 기본 데이터 생성
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({}, f)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_data = load_user_data()

    def save_user_data(self):
        with open("config/economy.json", "w", encoding='utf-8') as f:
            json.dump(self.user_data, f, indent=4)

    def get_balance(self, user_id):
        return self.user_data.get(user_id, {"cash": 0, "bank": 0, "attendance_bonus": 0})

    # 유저 계좌 개설 명령어
    @app_commands.command(name="개좌개설", description="계좌를 개설합니다.")
    async def create_account(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        if user_id in self.user_data:
            await interaction.response.send_message(f"{interaction.user.mention}님, 이미 계좌가 존재합니다.")
            return

        # 계좌 개설
        self.user_data[user_id] = {"cash": 0, "bank": 31000000, "attendance_bonus": 0}
        self.save_user_data()

        await interaction.response.send_message(f"{interaction.user.mention}님, 계좌가 성공적으로 개설되었습니다!")

    # 잔액 확인
    @app_commands.command(name="잔액확인", description="나의 잔액을 확인합니다.")
    async def balance(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        data = self.get_balance(user_id)

        embed = discord.Embed(title="💰 나의 재산 상태", color=discord.Color.green())
        embed.add_field(name="현금", value=f"{data['cash']} 원", inline=False)
        embed.add_field(name="은행 잔액", value=f"{data['bank']} 원", inline=False)
        embed.add_field(name="출석 보상", value=f"{data['attendance_bonus']} 원", inline=False)

        await interaction.response.send_message(embed=embed)

    # 입금 명령어
    @app_commands.command(name="입금", description="은행에 금액을 입금합니다.")
    async def deposit(self, interaction: discord.Interaction, amount: int):
        user_id = str(interaction.user.id)
        data = self.get_balance(user_id)

        if data["cash"] < amount:
            await interaction.response.send_message("현금이 부족합니다.", ephemeral=True)
            return

        data["cash"] -= amount
        data["bank"] += amount
        self.user_data[user_id] = data
        self.save_user_data()

        await interaction.response.send_message(f"{interaction.user.mention}님, {amount} 원을 은행에 입금했습니다.")
        with open(LOG_FILE_PATH, "a") as log_file:
            log_file.write(
                f"[{time.ctime()}] {interaction.user} deposited {amount} points. Bank balance: {data['bank']}\n")

    # 출금 명령어
    @app_commands.command(name="출금", description="은행에서 돈을 출금합니다.")
    async def withdraw(self, interaction: discord.Interaction, amount: int):
        user_id = str(interaction.user.id)
        data = self.get_balance(user_id)

        if data["bank"] < amount:
            await interaction.response.send_message("잔액이 부족합니다.", ephemeral=True)
            return

        data["bank"] -= amount
        data["cash"] += amount
        self.user_data[user_id] = data
        self.save_user_data()

        await interaction.response.send_message(f"{interaction.user.mention}님, {amount} 원을 은행 에서 출금 했습니다.")
        with open(LOG_FILE_PATH, "a") as log_file:
            log_file.write(f"[{time.ctime()}] {interaction.user} withdrew {amount} points. Cash: {data['cash']}\n")

    # 관리자가 금액을 추가하는 명령어
    @app_commands.command(name="add_money", description="관리자 전용: 유저 에게 돈을 추가 합니다.")
    async def admin_add_money(self, interaction: discord.Interaction, target: discord.User, amount: int):
        if not is_admin(interaction.user):  # 관리자 확인
            await interaction.response.send_message("이 명령어 는 어드민 만 사용할 수 있습니다.", ephemeral=True)
            return

        user_id = str(target.id)
        data = self.get_balance(user_id)

        data["cash"] += amount  # 현금에 추가
        self.user_data[user_id] = data
        self.save_user_data()

        await interaction.response.send_message(f"{interaction.user.mention}님, {target.mention}에게 {amount} 원을 추가했습니다.")
        with open(LOG_FILE_PATH, "a") as log_file:
            log_file.write(
                f"[{time.ctime()}] {interaction.user} added {amount} points to {target}. Cash: {data['cash']}\n")

    # 일일 보너스 명령어
    @app_commands.command(name="일일보너스", description="일일 보너스를 받습니다.")
    async def attendance_bonus(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        data = self.get_balance(user_id)

        daily_bonus = 10000000
        data["attendance_bonus"] += daily_bonus
        data["cash"] += daily_bonus
        self.user_data[user_id] = data
        self.save_user_data()

        await interaction.response.send_message(
            f"{interaction.user.mention}님, 오늘의 일일 보너스로 {daily_bonus} 원이 추가되었습니다. 현재 현금: {data['cash']} 원")
        with open(LOG_FILE_PATH, "a") as log_file:
            log_file.write(
                f"[{time.ctime()}] {interaction.user} received attendance bonus: {daily_bonus} points. Cash: {data['cash']}\n")

    # 슬래시 커맨드 동기화
    async def sync_commands(self):
        await self.bot.tree.sync()  # 슬래시 커맨드 동기화


# `setup` 함수에서 코그 로딩 후 슬래시 커맨드 동기화 호출
async def setup(bot):
    await bot.add_cog(Economy(bot))
    await bot.get_cog("Economy").sync_commands()  # 슬래시 커맨드 동기화
