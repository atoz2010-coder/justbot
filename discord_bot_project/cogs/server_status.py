import discord
from discord.ext import commands
import time

LOG_FILE_PATH = "logs/server_status_logs.txt"


class ServerStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="서버상태알림", description="Update the server status message.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def server_status(self, interaction: discord.Interaction, status_message: str):
        # 서버 상태 메시지를 업데이트하는 로직
        await interaction.response.send_message(f"서버 상태 업데이트: {status_message}")

        with open(LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(f"[{time.ctime()}] {interaction.user} 서버 상태 업데이트: {status_message}\n")

  # 슬래시 커맨드 동기화
    async def sync_commands(self):
        await self.bot.tree.sync()  # 슬래시 커맨드 동기화


# `setup` 함수에서 코그 로딩 후 슬래시 커맨드 동기화 호출
async def setup(bot):
    await bot.add_cog(Economy(bot))
    await bot.get_cog("server_status").sync_commands()  # 슬래시 커맨드 동기화

async def setup(bot):
    await bot.add_cog(ServerStatus(bot))
