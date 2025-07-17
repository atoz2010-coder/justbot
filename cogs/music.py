import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import datetime
import os

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 메인 bot에서 주입된 함수들
        self.get_db_connection = bot.get_db_connection
        self.get_server_config = bot.get_server_config

    @app_commands.command(name="들어와", description="봇을 음성 채널로 초대합니다.")
    @app_commands.guild_only()
    async def join(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            await interaction.response.send_message("❌ 음성 채널에 먼저 들어와야 봇을 초대할 수 있습니다!", ephemeral=True)
            return
        channel = interaction.user.voice.channel
        try:
            await channel.connect()
            await interaction.response.send_message(f"✅ {channel.name} 채널에 들어왔어요! 🎧")
        except discord.ClientException:
            await interaction.response.send_message("❌ 이미 음성 채널에 있습니다!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ 음성 채널에 들어갈 권한이 없습니다!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ 음성 채널 연결 실패: {e}", ephemeral=True)

    @app_commands.command(name="나가", description="봇을 음성 채널에서 내보냅니다.")
    @app_commands.guild_only()
    async def leave(self, interaction: discord.Interaction):
        if not interaction.guild.voice_client:
            await interaction.response.send_message("❌ 음성 채널에 없습니다!", ephemeral=True)
            return
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("✅ 음성 채널에서 나왔습니다! 👋")

    @app_commands.command(name="재생", description="지정된 로컬 오디오 파일을 재생합니다. (경로 필요)")
    @app_commands.describe(파일경로="재생할 오디오 파일의 경로 (예: music/song.mp3)")
    @app_commands.guild_only()
    async def play(self, interaction: discord.Interaction, 파일경로: str):
        if not interaction.guild.voice_client:
            await interaction.response.send_message("❌ 음성 채널에 먼저 봇을 초대해주세요! (`/들어와`)", ephemeral=True)
            return
        voice_client = interaction.guild.voice_client
        if not os.path.exists(파일경로):
            await interaction.response.send_message(f"❌ '{파일경로}' 파일을 찾을 수 없습니다! 경로를 확인해주세요!", ephemeral=True)
            return
        if voice_client.is_playing():
            voice_client.stop()
        try:
            FFMPEG_OPTIONS = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn'
            }
            source = discord.FFmpegPCMAudio(source=파일경로, **FFMPEG_OPTIONS)
            voice_client.play(source, after=lambda e: print(f'플레이어 에러: {e}') if e else None)
            await interaction.response.send_message(f"🎶 '{os.path.basename(파일경로)}'을(를) 재생합니다!")
        except Exception as e:
            await interaction.response.send_message(f"❌ 음악 재생 중 오류 발생: {e}\n(ffmpeg이 설치되어 있고 PATH에 추가되었는지 확인해주세요!)", ephemeral=True)

    @app_commands.command(name="정지", description="재생 중인 음악을 정지합니다.")
    @app_commands.guild_only()
    async def stop(self, interaction: discord.Interaction):
        if not interaction.guild.voice_client:
            await interaction.response.send_message("❌ 음성 채널에 없습니다!", ephemeral=True)
            return
        voice_client = interaction.guild.voice_client
        if voice_client.is_playing():
            voice_client.stop()
            await interaction.response.send_message("⏹️ 음악을 정지했습니다.")
        else:
            await interaction.response.send_message("❌ 재생 중인 음악이 없습니다!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Music(bot))