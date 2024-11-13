import discord
from discord.ext import commands
import json
import time

LOG_FILE_PATH = "logs/faq_logs.txt"


class FAQ(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.faq_data = self.load_faq_data()

    def load_faq_data(self):
        try:
            with open("config/faq.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_faq_data(self):
        with open("config/faq.json", "w", encoding="utf-8") as f:
            json.dump(self.faq_data, f, ensure_ascii=False, indent=4)

    @discord.app_commands.command(name="faq", description="Get an answer to a frequently asked question.")
    async def faq(self, interaction: discord.Interaction, question: str):
        answer = self.faq_data.get(question.lower())
        if answer:
            await interaction.response.send_message(f"**{question}**: {answer}")
        else:
            await interaction.response.send_message(f"**{question}**에 대한 답변이 없습니다.")

        with open(LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(f"[{time.ctime()}] {interaction.user} FAQ 요청: {question}\n")

    @discord.app_commands.command(name="add_faq", description="Add a new FAQ question and answer.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def add_faq(self, interaction: discord.Interaction, question: str, answer: str):
        self.faq_data[question.lower()] = answer
        self.save_faq_data()
        await interaction.response.send_message(f"새 자주 묻는 질문 추가됨: **{question}** - {answer}")

        with open(LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(f"[{time.ctime()}] {interaction.user} FAQ 추가: {question} - {answer}\n")

    # 슬래시 커맨드 동기화
    async def sync_commands(self):
        await self.bot.tree.sync()  # 슬래시 커맨드 동기화


# `setup` 함수에서 코그 로딩 후 슬래시 커맨드 동기화 호출
async def setup(bot):
    await bot.add_cog(Economy(bot))
    await bot.get_cog("faq").sync_commands()  # 슬래시 커맨드 동기화


async def setup(bot):
    await bot.add_cog(FAQ(bot))
