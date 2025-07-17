import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import datetime
import random


class Game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.get_db_connection = bot.get_db_connection

    @app_commands.command(name="주사위", description="주사위를 굴립니다.")
    @app_commands.describe(면="주사위의 면 개수 (기본 6면)")
    @app_commands.guild_only()
    async def roll_dice(self, interaction: discord.Interaction, 면: int = 6):
        if 면 <= 1:
            await interaction.response.send_message("❌ 주사위 면은 2개 이상이어야 합니다!", ephemeral=True)
            return
        result = random.randint(1, 면)

        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
                       INSERT INTO game_stats (game_type, user_id, username, sides, result, timestamp)
                       VALUES (?, ?, ?, ?, ?, ?)
                       """, ("주사위", str(interaction.user.id), interaction.user.display_name, 면, str(result),
                             datetime.datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()

        await interaction.response.send_message(
            f"🎲 {interaction.user.display_name}님이 {면}면 주사위를 굴려 **{result}**가 나왔습니다!")

    @app_commands.command(name="가위바위보", description="봇과 가위바위보를 합니다.")
    @app_commands.describe(선택="가위, 바위, 보 중 하나를 선택하세요.")
    @app_commands.guild_only()
    async def rps(self, interaction: discord.Interaction, 선택: str):
        choices = ["가위", "바위", "보"]
        bot_choice = random.choice(choices)

        user_choice_normalized = 선택.strip().lower()

        if user_choice_normalized not in choices:
            await interaction.response.send_message("❌ '가위', '바위', '보' 중에 하나를 선택해주세요!", ephemeral=True)
            return

        result_message = f"🤔 {interaction.user.display_name}님은 **{user_choice_normalized}**, 저는 **{bot_choice}**를 냈습니다!\n"
        game_result = ""

        if user_choice_normalized == bot_choice:
            result_message += "🤝 비겼습니다! 다시 한 번 시도해 보세요!"
            game_result = "무승부"
        elif (user_choice_normalized == "가위" and bot_choice == "보") or \
                (user_choice_normalized == "바위" and bot_choice == "가위") or \
                (user_choice_normalized == "보" and bot_choice == "바위"):
            result_message += "🎉 이겼습니다! 축하합니다!"
            game_result = "승리"
        else:
            result_message += "😭 제가 이겼습니다! 다음엔 꼭 이겨보세요!"
            game_result = "패배"

        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
                       INSERT INTO game_stats (game_type, user_id, username, user_choice, bot_choice, result, timestamp)
                       VALUES (?, ?, ?, ?, ?, ?, ?)
                       """, ("가위바위보", str(interaction.user.id), interaction.user.display_name, user_choice_normalized,
                             bot_choice, game_result, datetime.datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()

        await interaction.response.send_message(result_message)


async def setup(bot):
    await bot.add_cog(Game(bot))