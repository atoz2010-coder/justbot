import discord
from discord.ext import commands
import os
import json

# 설정 파일 로드
with open('config/config.json') as f:
    config = json.load(f)

# 봇 초기화
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 봇이 준비되었을 때 슬래시 커맨드 동기화
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ 슬래시 커맨드 동기화됨: {len(synced)} 개의 커맨드")
    except Exception as e:
        print(f"슬래시 커맨드 동기화 실패: {e}")

    print(f'✅ Logged in as {bot.user}!')
    print('봇 준비 완료')

    # 모든 Cog 로드
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'Loaded cog: {filename[:-3]}')
            except Exception as e:
                print(f"Failed to load cog {filename[:-3]}: {e}")

    # 슬래시 커맨드 동기화
    try:
        await bot.tree.sync()
        print(f"✅ 슬래시 커맨드 동기화 완료!")
    except Exception as e:
        print(f"슬래시 커맨드 동기화 중 오류 발생: {e}")

# 자동 역할 부여 (예: 미인증 역할)
@bot.event
async def on_member_join(member):
    unverified_role = discord.utils.get(member.guild.roles, id=int(config["unverified_role_id"]))
    if unverified_role:
        await member.add_roles(unverified_role)
        await member.send("zgvrp 서버에 오신 것을 환영합니다! 인증을 완료해 주세요. 인증은 티켓툴, 불록링크 봇으로 해주세요 2개에요")
    print(f'New member joined: {member.name}, assigned unverified role.')

# 봇의 Cog를 추가하는 setup 함수
async def setup(bot):
    await bot.add_cog(ServerStatus(bot))
    await bot.add_cog(Warning(bot))  # Warning Cog 추가
    await bot.add_cog(Economy(bot))  # Economy Cog 추가
    await bot.add_cog(FAQ(bot))  # FAQ Cog 추가
    await bot.add_cog(Music(bot))  # Music Cog 추가

    # Cog가 모두 로드된 후 슬래시 커맨드 동기화
    try:
        await bot.tree.sync()
        print(f"✅ 슬래시 커맨드 동기화 완료!")
    except Exception as e:
        print(f"슬래시 커맨드 동기화 중 오류 발생: {e}")

# 봇 시작
bot.run(config["token"])
