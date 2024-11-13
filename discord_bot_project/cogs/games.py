import discord
from discord.ext import commands
import random
import time

LOG_FILE_PATH = "logs/games_logs.txt"


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="roll_dice", description="Roll a dice and get a result between 1 and 6.")
    async def roll_dice(self, interaction: discord.Interaction):
        result = random.randint(1, 6)
        await interaction.response.send_message(f"{interaction.user.mention} 주사위 결과: {result}")

        with open(LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(f"[{time.ctime()}] {interaction.user} 주사위 굴림: {result}\n")

    @discord.app_commands.command(name="flip_coin", description="Flip a coin and get heads or tails.")
    async def flip_coin(self, interaction: discord.Interaction):
        result = random.choice(["앞면", "뒷면"])
        await interaction.response.send_message(f"{interaction.user.mention} 동전 던지기 결과: {result}")

        with open(LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(f"[{time.ctime()}] {interaction.user} 동전 던지기: {result}\n")

    # 슬래시 커맨드 동기화
    async def sync_commands(self):
        await self.bot.tree.sync()  # 슬래시 커맨드 동기화


# `setup` 함수에서 코그 로딩 후 슬래시 커맨드 동기화 호출
async def setup(bot):
    await bot.add_cog(Economy(bot))
    await bot.get_cog("games").sync_commands()  # 슬래시 커맨드 동기화


async def setup(bot):
    await bot.add_cog(Games(bot))
