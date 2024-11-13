import discord
from discord.ext import commands
import time

LOG_FILE_PATH = "logs/warning_logs.txt"


class Warning(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_warnings = {}

    @discord.app_commands.command(name="경고주기", description="유저에게 경고를 줍니다.(경고 채널에서만 사용)")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "사유 없음"):
        # 경고 기능 구현
        warning_count = self.user_warnings.get(member.id, 0) + 1
        self.user_warnings[member.id] = warning_count

        if warning_count >= 8:
            await member.timeout(duration=3600)  # Timeout for 1 hour
            await interaction.response.send_message(f"{member.mention}님이 1시간 동안 타임아웃 처리되었습니다. 이유: {reason}")
        else:
            await interaction.response.send_message(f"{member.mention}님에게 경고가 부여되었습니다. 이유: {reason}")

        with open(LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(f"[{time.ctime()}] {interaction.user} {member}에게 경고: {reason}\n")

    @discord.app_commands.command(name="경고제거", description="유저에게 경고를 회수해요~ (경고체널에서만 사용해요)")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def remove_warn(self, interaction: discord.Interaction, member: discord.Member):
        # 경고 회수 기능 구현
        warning_count = self.user_warnings.get(member.id, 0)

        if warning_count > 0:
            warning_count -= 1
            self.user_warnings[member.id] = warning_count
            await interaction.response.send_message(f"{member.mention}님의 경고가 하나 회수되었습니다. 현재 경고 수: {warning_count}")

            with open(LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
                log_file.write(f"[{time.ctime()}] {interaction.user} {member}에게서 경고 회수\n")
        else:
            await interaction.response.send_message(f"{member.mention}님에게 회수할 경고가 없습니다.")

    @discord.app_commands.command(name="타임아웃", description="유저에게 타임아웃을 적용해요 경고채널에서만 사용")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, duration: int,
                      reason: str = "사유 없음"):
        # 타임아웃 기능 구현
        try:
            timeout_duration = duration * 60  # Convert minutes to seconds
            await member.timeout(duration=timeout_duration)
            await interaction.response.send_message(f"{member.mention}님이 {duration}분 동안 타임아웃 처리되었습니다. 이유: {reason}")

            with open(LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
                log_file.write(f"[{time.ctime()}] {interaction.user} {member}에게 타임아웃 부여: {duration}분, 이유: {reason}\n")
        except Exception as e:
            await interaction.response.send_message(f"타임아웃 처리 중 오류가 발생했습니다: {e}")

    # 슬래시 커맨드 동기화
    async def sync_commands(self):
        await self.bot.tree.sync()  # 슬래시 커맨드 동기화


# `setup` 함수에서 코그 로딩 후 슬래시 커맨드 동기화 호출
async def setup(bot):
    await bot.add_cog(Economy(bot))
    await bot.get_cog("warning").sync_commands()  # 슬래시 커맨드 동기화


async def setup(bot):
    await bot.add_cog(Warning(bot))
