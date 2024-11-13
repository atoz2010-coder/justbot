import discord
from discord.ext import commands
import time

LOG_FILE_PATH = "logs/roblox_logs.txt"


class Roblox(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="robloxprofile", description="유저네임 얻기")
    async def roblox_profile(self, interaction: discord.Interaction, username: str):
        # 로블록스 프로필 정보를 가져오는 로직을 여기에 구현합니다.
        await interaction.response.send_message(f"{interaction.user.mention} 요청하신 로블록스 프로필: {username}")

        with open(LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(f"[{time.ctime()}] {interaction.user} 로블록스 프로필 요청: {username}\n")

    # 슬래시 커맨드 동기화
    async def sync_commands(self):
        await self.bot.tree.sync()  # 슬래시 커맨드 동기화


# `setup` 함수에서 코그 로딩 후 슬래시 커맨드 동기화 호출
async def setup(bot):
    await bot.add_cog(Economy(bot))
    await bot.get_cog("roblox").sync_commands()  # 슬래시 커맨드 동기화


async def setup(bot):
    await bot.add_cog(Roblox(bot))
