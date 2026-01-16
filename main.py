import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from utils.database import Database
from utils.scheduler import ReminderScheduler
from cogs.admin import AdminCog
from cogs.notifications import NotificationsCog
from cogs.activity import ActivityCog
from cogs.ai import AICog

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("DISCORD_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []
DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/reminders.json")

if not TOKEN:
    logger.error("DISCORD_TOKEN не установлен в .env файле")
    exit(1)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

db = Database(DATABASE_PATH)
scheduler = ReminderScheduler()


@bot.event
async def on_ready():
    scheduler.start()

    for guild in bot.guilds:
        reminders = db.get_reminders()
        for reminder in reminders:
            notifications_cog = bot.get_cog("NotificationsCog")
            if notifications_cog:
                notifications_cog.schedule_reminder(reminder, guild.id)

    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name="готовит шаурму"
    )
    await bot.change_presence(activity=activity)


@bot.event
async def on_guild_join(guild):
    logger.info(f"➕ Бот присоединился к серверу: {guild.name} (ID: {guild.id})")

    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            embed = discord.Embed(
                title="👋 Привет!",
                description="Спасибо за добавление меня на сервер!",
                color=discord.Color.green()
            )
            try:
                await channel.send(embed=embed)
                break
            except:
                continue


@bot.event
async def on_error(event, *args, **kwargs):
    logger.error(f"Error in {event}:", exc_info=True)


async def load_cogs():
    logger.info("Загрузка расширений...")

    admin_cog = AdminCog(bot, db, scheduler, ADMIN_IDS)
    notifications_cog = NotificationsCog(bot, db, scheduler)
    activity_cog = ActivityCog(bot, db)
    ai_cog = AICog(bot)

    await bot.add_cog(admin_cog)
    await bot.add_cog(notifications_cog)
    await bot.add_cog(activity_cog)
    await bot.add_cog(ai_cog)


async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)


if __name__ == "__main__":
    import asyncio

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
        scheduler.stop()
