import discord
from discord.ext import commands
import asyncio
import time

LOG_FILE_PATH = "logs/music_logs.txt"


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="재생", description="Play music from a URL.")
    async def play_music(self, interaction: discord.Interaction, url: str):
        # Implement your music playing logic here
        await interaction.response.send_message(f"{interaction.user.mention} 요청하신 음악을 재생 중입니다: {url}")

        with open(LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(f"[{time.ctime()}] {interaction.user} 음악 재생: {url}\n")

    @discord.app_commands.command(name="정지", description="Stop the currently playing music.")
    async def stop_music(self, interaction: discord.Interaction):
        # Implement your music stopping logic here
        await interaction.response.send_message(f"{interaction.user.mention} 음악이 중지되었습니다.")

        with open(LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(f"[{time.ctime()}] {interaction.user} 음악 중지\n")

    # 슬래시 커맨드 동기화
    async def sync_commands(self):
        await self.bot.tree.sync()  # 슬래시 커맨드 동기화


# `setup` 함수에서 코그 로딩 후 슬래시 커맨드 동기화 호출
async def setup(bot):
    await bot.add_cog(Economy(bot))
    await bot.get_cog("music").sync_commands()  # 슬래시 커맨드 동기화


async def setup(bot):
    await bot.add_cog(Music(bot))
