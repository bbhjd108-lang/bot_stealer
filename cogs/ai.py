import discord
from discord.ext import commands
from discord import app_commands
import logging

logger = logging.getLogger(__name__)

MODELS = [
    "gpt-4o-mini",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-3-flash",
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-0125",
    "gpt-4",
    "gpt-4-turbo",
    "gpt-4o",
    "gpt-4.1",
    "grok-3"
]


class AICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_ai_response(self, text: str):
        try:
            from openai import OpenAI
        except ImportError:
            logger.error("OpenAI библиотека не установлена. Установи: pip install openai")
            return "❌ Ошибка: OpenAI библиотека не установлена"

        client = OpenAI(
            base_url="https://api.onlysq.ru/ai/openai",
            api_key="openai",
        )

        for model in MODELS:
            try:
                logger.info(f"Попытка использовать модель: {model}")
                
                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "user",
                            "content": text,
                        },
                    ],
                    max_tokens=1000,
                    timeout=30
                )
                
                response = completion.choices[0].message.content
                logger.info(f"✅ Успешно использована модель: {model}")
                return response
                
            except Exception as e:
                logger.debug(f"Модель {model} не работает: {e}")
                continue

        return "❌ Не удалось получить ответ ни от одной ИИ модели"

    @app_commands.command(name="ai", description="Спросить у ИИ")
    @app_commands.describe(text="Ваш вопрос или текст для ИИ")
    async def ai(self, interaction: discord.Interaction, text: str):
        await interaction.response.defer()

        try:
            response = await self.get_ai_response(text)
            
            if len(response) > 2000:
                chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                
                for chunk in chunks:
                    await interaction.followup.send(chunk)
            else:
                await interaction.followup.send(response)
                
        except Exception as e:
            logger.error(f"Ошибка при обработке AI команды: {e}")
            await interaction.followup.send(f"❌ Ошибка: {str(e)}")


async def setup(bot):
    await bot.add_cog(AICog(bot))
