import os
import discord
import asyncio
from discord.ui import Modal, InputText, View, button
from datetime import datetime
from formEmbed import SurveyModal
from infoEmbed import infoEmbed, ApplicationButton

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

bot = discord.Bot()
    
@bot.command()
async def close(ctx: discord.ApplicationContext):
    await ctx.respond("🔒Закрываю ветку...")
    thread = ctx.channel
    await thread.edit(archived = True, locked = True)
    await ctx.edit(content="✅ Ветка закрыта!")
    thread_url = thread.jump_url
    channel = bot.get_channel(1474832617437397073)
    await channel.send(f"Заявка была закрыта. [Открыть ветку]({thread_url})")

@bot.command()
@discord.default_permissions(manage_messages=True)
async def embed(ctx:discord.ApplicationContext):
    await ctx.send(embed = infoEmbed(), view=ApplicationButton(bot))

@bot.event
async def on_ready():
    print(f"✅ Бот {bot.user} запущен!")
    bot.add_view(ApplicationButton(bot))

bot.run(os.getenv('DISCORD_TOKEN'))
