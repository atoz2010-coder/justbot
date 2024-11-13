
import discord
from discord import app_commands
from discord.ext import commands
from collections import defaultdict
import time

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 사용자별 메시지 타임스탬프 기록 (메시지 전송 시간)
        self.message_logs = defaultdict(list)
        # 사용자별 경고 횟수 기록
        self.warnings = defaultdict(int)
        # 자동 차단 기준 (경고 횟수)
        self.max_warnings = 14
        # 메시지 스팸 기준 설정
        self.spam_threshold = 10  # 10초 내 5회 메시지
        self.time_window = 10  # 초 단위로 스팸 체크 시간 간격

    @commands.Cog.listener()
    async def on_message(self, message):
        # 봇의 메시지, 관리자 권한 메시지는 무시
        if message.author.bot or message.author.guild_permissions.administrator:
            return

        # 현재 시간 (초 단위)
        current_time = time.time()
        # 사용자별 메시지 기록 리스트
        user_logs = self.message_logs[message.author.id]
        user_logs.append(current_time)

        # 지정된 시간 창 내의 메시지만 유지
        user_logs = [timestamp for timestamp in user_logs if current_time - timestamp < self.time_window]
        self.message_logs[message.author.id] = user_logs

        # 스팸 감지: 지정된 시간 창 내 메시지 수가 기준을 초과하는지 확인
        if len(user_logs) > self.spam_threshold:
            # 경고 카운트 증가
            self.warnings[message.author.id] += 1
            warning_count = self.warnings[message.author.id]

            await message.channel.send(
                f"{message.author.mention} 스팸이 감지되어 경고가 부여되었습니다. (경고 {warning_count}/{self.max_warnings})"
            )

            # 최대 경고 횟수 초과 시 사용자 자동 차단
            if warning_count >= self.max_warnings:
                try:
                    await message.guild.ban(
                        message.author, reason="자동 차단 - 봇의 설정대로 일정 경고 넘음"
                    )
                    await message.channel.send(
                        f"{message.author.mention}님이 차단되었습니다."
                    )
                except discord.Forbidden:
                    await message.channel.send("봇에 사용자 차단 권한이 없습니다.")

                # 차단 후 사용자 기록 제거
                del self.message_logs[message.author.id]
                del self.warnings[message.author.id]
        else:
            # 명령어를 처리할 수 있도록 메시지 이벤트를 넘김
            await self.bot.process_commands(message)

    @app_commands.command(name="경고초기화", description="사용자의 경고를 초기화합니다 (관리자 전용).")
    @app_commands.checks.has_permissions(administrator=True)
    async def reset_warnings(self, interaction: discord.Interaction, member: discord.Member):
        # 경고 초기화
        if member.id in self.warnings:
            del self.warnings[member.id]
            await interaction.response.send_message(f"{member.mention}의 경고 기록이 초기화되었습니다.")
        else:
            await interaction.response.send_message(f"{member.mention}에게 부여된 경고 기록이 없습니다.")

    @app_commands.command(name="경고확인", description="사용자의 현재 경고 횟수를 확인합니다.")
    async def check_warnings(self, interaction: discord.Interaction, member: discord.Member):
        # 경고 횟수 확인
        warning_count = self.warnings.get(member.id, 0)
        await interaction.response.send_message(f"{member.mention}의 현재 경고 횟수는 {warning_count}회입니다.")

    # 슬래시 커맨드 동기화
    async def sync_commands(self):
        await self.bot.tree.sync()  # 슬래시 커맨드 동기화


# `setup` 함수에서 코그 로딩 후 슬래시 커맨드 동기화 호출
async def setup(bot):
    await bot.add_cog(Economy(bot))
    await bot.get_cog("automod").sync_commands()  # 슬래시 커맨드 동기화


# setup 함수: Cog 로드 시 봇에 추가
async def setup(bot):
    await bot.add_cog(AutoMod(bot))
