import discord
from discord.ext import commands
import time

LOG_FILE_PATH = "logs/roles_logs.txt"


class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="역할넣기", description="Assign a role to a member.")
    @discord.app_commands.checks.has_permissions(manage_roles=True)
    async def assign_role(self, interaction: discord.Interaction, member: discord.Member, role_name: str):
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        if role:
            await member.add_roles(role)
            await interaction.response.send_message(f"{member.mention}에게 역할 {role_name}을/를 부여했습니다.")

            with open(LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
                log_file.write(f"[{time.ctime()}] {interaction.user} {member}에게 역할 부여: {role_name}\n")
        else:
            await interaction.response.send_message(f"{role_name} 역할을 찾을 수 없습니다.")

    # 슬래시 커맨드 동기화
    async def sync_commands(self):
        await self.bot.tree.sync()  # 슬래시 커맨드 동기화


# `setup` 함수에서 코그 로딩 후 슬래시 커맨드 동기화 호출
async def setup(bot):
    await bot.add_cog(Economy(bot))
    await bot.get_cog("roles").sync_commands()  # 슬래시 커맨드 동기화


async def setup(bot):
    await bot.add_cog(Roles(bot))
