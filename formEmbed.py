import os
import discord
import asyncio
from discord.ui import Modal, InputText, View, Button
from datetime import datetime
from mcrcon import MCRcon

# ─── RCON конфиг ────────────────────────────────────────────────────────────
RCON_HOST = os.getenv('RCON_HOST')
RCON_PORT = int(os.getenv('RCON_PORT'))
RCON_PASSWORD = os.getenv('RCON_PASSWORD')
# ─── Добавление в whitelist через RCON ──────────────────────────────────────
async def assign_role(member: discord.Member, role_id: int):
    role = member.guild.get_role(role_id)
    await member.add_roles(role, reason="Заявка принята")

def add_to_whitelist(nickname: str) -> bool:
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            response = mcr.command(f"whitelist add {nickname}")
            print(f"[RCON] whitelist add {nickname}: {response}")
            return True
    except Exception as e:
        print(f"[RCON] Ошибка при добавлении в whitelist: {e}")
        return False

# ─── Кнопка для просмотра ветки ─────────────────────────────────────────────
class ViewThreadButton(View):
    def __init__(self, thread_url: str):
        super().__init__(timeout=None)
        button = Button(
            label="Посмотреть ветку",
            style=discord.ButtonStyle.link,
            url=thread_url,
            emoji="🔗"
        )
        self.add_item(button)

# ─── Кнопки внутри ветки (финальное решение) ────────────────────────────────
class ThreadButtons(View):
    def __init__(self, main_message_id: int, main_channel_id: int, bot, thread: discord.Thread):
        super().__init__(timeout=None)
        self.main_message_id = main_message_id
        self.main_channel_id = main_channel_id
        self.bot = bot
        self.thread = thread
        
        accept_button = Button(
            label="Принять",
            style=discord.ButtonStyle.success,
            custom_id=f"thread_accept_{main_message_id}"
        )
        reject_button = Button(
            label="Отклонить",
            style=discord.ButtonStyle.danger,
            custom_id=f"thread_reject_{main_message_id}"
        )
        
        accept_button.callback = self.accept_callback
        reject_button.callback = self.reject_callback
        
        self.add_item(accept_button)
        self.add_item(reject_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        required_role = discord.utils.get(interaction.guild.roles, name="Whitelist-Модератор")
        if required_role not in interaction.user.roles:
            await interaction.response.send_message(
                "❌ Только Whitelist-модераторы могут использовать эти кнопки!",
                ephemeral=True
            )
            return False
        return True
    
    async def accept_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        channel = self.bot.get_channel(self.main_channel_id)
        if channel:
            try:
                main_message = await channel.fetch_message(self.main_message_id)
                if main_message and main_message.embeds:
                    main_embed = main_message.embeds[0]

                    applicant_mention = None
                    minecraft_nickname = None

                    # Достаём никнейм и упоминание из полей embed'а
                    for field in main_embed.fields:
                        if field.name == "Отправитель":
                            applicant_mention = field.value
                        if field.name == "👤 Никнейм":
                            minecraft_nickname = field.value

                    main_embed.title = "✅ Принято"
                    main_embed.color = discord.Color.green()
                    main_embed.add_field(
                        name="Финальное решение",
                        value=f"✅ Принято: {interaction.user.mention}",
                        inline=False
                    )

                    view = ViewThreadButton(self.thread.jump_url)
                    await main_message.edit(embed=main_embed, view=view)

                    if applicant_mention:
                        try:
                            applicant_id = int(applicant_mention.strip('<@!>'))

                            # Меняем ник игрока в Discord на его Minecraft-никнейм
                            member = interaction.guild.get_member(applicant_id)
                            if member is None:
                                member = await interaction.guild.fetch_member(applicant_id)

                            nick_status = "⚠️ Ник не найден в анкете"
                            wl_status = "⚠️ Ник не найден в анкете"

                            if minecraft_nickname:
                                # Смена ника в Discord
                                try:
                                    await member.edit(nick=minecraft_nickname)
                                    nick_status = f"✅ Ник изменён на `{minecraft_nickname}`"
                                    print(f"✅ Ник изменён: {member.name} → {minecraft_nickname}")
                                except discord.Forbidden:
                                    nick_status = "⚠️ Нет прав для смены ника (у владельца сервера нельзя)"
                                    print(f"❌ Нет прав для смены ника у {member.name}")
                                except Exception as e:
                                    nick_status = f"⚠️ Ошибка смены ника: {e}"
                                    print(f"❌ Ошибка смены ника: {e}")

                                # Добавляем в whitelist через RCON
                                wl_success = add_to_whitelist(minecraft_nickname)
                                wl_status = (
                                    f"✅ `{minecraft_nickname}` добавлен в whitelist"
                                    if wl_success
                                    else "⚠️ Ошибка RCON — добавьте в whitelist вручную"
                                )
                                # Выдача роли
                                try:
                                    await assign_role(member, 1515311488171249694)  # 👈 ЗАМЕНИТЕ "Игрок" на вашу роль
                                    role_status = "✅ Выдана роль Игрок"
                                except Exception as e:
                                    role_status = f"⚠️ Ошибка выдачи роли: {e}"
                                    
                            # DM игроку
                            applicant = await self.bot.fetch_user(applicant_id)
                            dm_embed = discord.Embed(
                                title="✅ Ваша заявка принята!",
                                description="Поздравляем! Ваша заявка на сервер была одобрена.",
                                color=discord.Color.green()
                            )
                            dm_embed.add_field(
                                name="🎮 Как зайти на сервер",
                                value="IP: **mc.piggycraft.online**\nВерсия: **1.21.11**",
                                inline=False
                            )
                            await applicant.send(embed=dm_embed)
                            print(f"✅ ЛС отправлено {applicant.name}")

                            await interaction.followup.send(
                                f"✅ Заявка финально принята!\n"
                                f"🏷️ {nick_status}\n"
                                f"📋 {wl_status}",
                                ephemeral=True
                            )

                        except Exception as e:
                            print(f"❌ Ошибка: {e}")
                            await interaction.followup.send(
                                f"✅ Принято, но возникла ошибка: {e}",
                                ephemeral=True
                            )
                    else:
                        await interaction.followup.send("✅ Заявка финально принята!", ephemeral=True)

            except Exception as e:
                print(f"Ошибка при изменении сообщения: {e}")
                await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)

        try:
            await self.thread.edit(archived=True, locked=True)
        except Exception as e:
            print(f"Ошибка при закрытии ветки: {e}")
    
    async def reject_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        channel = self.bot.get_channel(self.main_channel_id)
        if channel:
            try:
                main_message = await channel.fetch_message(self.main_message_id)
                if main_message and main_message.embeds:
                    main_embed = main_message.embeds[0]

                    applicant_mention = None
                    for field in main_embed.fields:
                        if field.name == "Отправитель":
                            applicant_mention = field.value
                            break
                    
                    main_embed.title = "❌ Отказано"
                    main_embed.color = discord.Color.red()
                    main_embed.add_field(
                        name="Финальное решение",
                        value=f"❌ Отказано модератором {interaction.user.mention}",
                        inline=False
                    )
                    
                    view = ViewThreadButton(self.thread.jump_url)
                    await main_message.edit(embed=main_embed, view=view)
                    
                    if applicant_mention:
                        try:
                            applicant_id = int(applicant_mention.strip('<@!>'))
                            applicant = await self.bot.fetch_user(applicant_id)
                            
                            dm_embed = discord.Embed(
                                title="❌ Ваша заявка отклонена",
                                description="К сожалению, ваша заявка на сервер была отклонена.",
                                color=discord.Color.red()
                            )
                            await applicant.send(embed=dm_embed)
                            print(f"✅ ЛС отправлено заявителю {applicant.name}")
                        except Exception as e:
                            print(f"❌ Не удалось отправить ЛС: {e}")
                            
            except Exception as e:
                print(f"Ошибка при изменении сообщения: {e}")
        
        await interaction.followup.send("❌ Заявка финально отклонена!", ephemeral=True)
        
        try:
            await self.thread.edit(archived=True, locked=True)
        except Exception as e:
            print(f"Ошибка при закрытии ветки: {e}")

# ─── Кнопки первичного просмотра заявки ─────────────────────────────────────
class FormButton(View):
    def __init__(self, applicant: discord.Member, bot, main_message_id: int, main_channel_id: int):
        super().__init__(timeout=None)
        self.applicant = applicant
        self.bot = bot
        self.main_message_id = main_message_id
        self.main_channel_id = main_channel_id
        
        acceptButton = Button(
            label="Принять", 
            style=discord.ButtonStyle.success,
            custom_id=f"accept_{main_message_id}"
        )
        cancelButton = Button(
            label="Отклонить", 
            style=discord.ButtonStyle.danger, 
            custom_id=f"cancel_{main_message_id}"
        )
        
        acceptButton.callback = self.accept_callback
        cancelButton.callback = self.cancel_callback
        
        self.add_item(acceptButton)
        self.add_item(cancelButton)
        
    async def accept_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        embed = interaction.message.embeds[0]
        embed.title = "✅ Принято в работу"
        embed.color = discord.Color.blue()
        embed.add_field(name="Взял в работу", value=interaction.user.mention, inline=False)
        
        channel = self.bot.get_channel(1448695893044891668)
        role = discord.utils.get(interaction.guild.roles, name="Whitelist-Модератор")
        
        thread = await channel.create_thread(
            name=f"Заявка {self.applicant.name}",
            auto_archive_duration=4320,
            invitable=False
        )
        
        # DM игроку — заявка принята в работу
        try:
            dm_embed = discord.Embed(
                title="📋 Ваша заявка принята в работу",
                description=f"Ваша заявка была принята модератором {interaction.user.mention} и теперь рассматривается.",
                color=discord.Color.blue()
            )
            dm_embed.add_field(
                name="⏳ Что дальше?",
                value="Модераторы зададут вам несколько вопросов в ветке. Пожалуйста, отвечайте там.",
                inline=False
            )
            await self.applicant.send(embed=dm_embed)
            print(f"✅ ЛС о начале рассмотрения отправлено {self.applicant.name}")
        except Exception as e:
            print(f"❌ Не удалось отправить ЛС о начале рассмотрения: {e}")
        
        thread_buttons = ThreadButtons(
            main_message_id=self.main_message_id,
            main_channel_id=self.main_channel_id,
            bot=self.bot,
            thread=thread
        )
        
        await thread.add_user(self.applicant)
        if role:
            await thread.send(f"||{role.mention}||")
        
        welcome_embed = discord.Embed(
            description=(
                f"## Заявка {self.applicant.name}\n"
                f"Ваша заявка была поставлена на рассмотрение. Чтобы попасть в вайт-лист, Вам необходимо ответить на несколько вопросов:\n"
                f"\n"
                f"1. Ознакомлены ли вы с правилами сервера?\n"
                f"2. Сколько вы планируете играть на сервере?\n"
                f"3. Почему вы выбрали именно наш проект?\n"
            ),
            color=discord.Color.green()
        )
        welcome_embed.add_field(name="Подал", value=f"{self.applicant.mention}")
        welcome_embed.add_field(name="Взял в работу", value=f"{interaction.user.mention}")
        welcome_embed.add_field(name="Время", value=f"{datetime.now().strftime('%d.%m.%Y %H:%M')}")
        
        await thread.send(embed=welcome_embed, view=thread_buttons)
        await interaction.message.edit(embed=embed, view=None)
        
        await interaction.followup.send(
            f"✅ Ветка создана: {thread.mention}\n",
            ephemeral=True
        )
        
    async def cancel_callback(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        embed.title = "❌ Отказано"
        embed.color = discord.Color.red()
        embed.add_field(name="Отклонил", value=interaction.user.mention, inline=False)
        await interaction.response.edit_message(embed=embed, view=None)
        
        # DM игроку — заявка отклонена без ветки
        try:
            dm_embed = discord.Embed(
                title="❌ Ваша заявка отклонена",
                description="К сожалению, ваша заявка на сервер была отклонена без создания ветки.",
                color=discord.Color.red()
            )
            dm_embed.add_field(
                name="📋 Возможные причины",
                value="• Недостаточно информации\n• Не подходит возраст\n• Нарушение правил подачи заявки или сервера.",
                inline=False
            )
            dm_embed.add_field(
                name="📝 Что дальше?",
                value="Вы можете купить платную проходку, чтобы зайти на сервер без заявки.",
                inline=False
            )
            await self.applicant.send(embed=dm_embed)
            print(f"✅ ЛС об отклонении отправлено {self.applicant.name}")
        except Exception as e:
            print(f"❌ Не удалось отправить ЛС об отклонении: {e}")

# ─── Модальное окно анкеты ───────────────────────────────────────────────────
class SurveyModal(Modal):
    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs, title="Заявка на сервер")
        self.bot = bot
        
        self.add_item(InputText(
            label="Ваш игровой никнейм",
            placeholder="Введите ник",
            min_length=3,
            max_length=20,
        ))
        self.add_item(InputText(
            label="Сколько вам лет?",
            placeholder="Введите возраст"
        ))
        self.add_item(InputText(
            label="Где вы узнали о сервере?"
        ))
        self.add_item(InputText(
            style=discord.InputTextStyle.long,
            label="Расскажите о себе",
            required=False
        ))
    
    async def callback(self, interaction: discord.Interaction):
        nickname = self.children[0].value
        age = self.children[1].value
        source = self.children[2].value
        about = self.children[3].value
        
        account_created = interaction.user.created_at.strftime("%d.%m.%Y %H:%M")
        joined_server = interaction.user.joined_at.strftime("%d.%m.%Y %H:%M")
        avatar_url = interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        applicant = interaction.user
        
        embed = discord.Embed(
            title="📝 Новая заявка!", 
            color=0x242429
        )
        
        embed.add_field(name="👤 Никнейм", value=nickname or "Не указано")
        embed.add_field(name="📊 Возраст", value=age or "Не указано")
        embed.add_field(name="🔍 Откуда узнал", value=source or "Не указано", inline=False)
        embed.add_field(name="📖 О себе", value=about or "Не указано", inline=False)
        embed.add_field(name="🕛 Время подачи заявки", value=current_time, inline=False)
        embed.add_field(name="📅 Дата создания", value=account_created)
        embed.add_field(name="📅 Дата вступления", value=joined_server)
        embed.add_field(name="Отправитель", value=interaction.user.mention, inline=False)
        embed.set_thumbnail(url=avatar_url)
        
        await interaction.response.send_message("✅ Заявка отправлена!", ephemeral=True)
        
        channelId = 1448710728415445134
        channel = interaction.client.get_channel(channelId)
        
        # Отправляем сообщение и получаем его ID
        message = await channel.send(
            embed=embed,
            view=FormButton(
                applicant=applicant,
                bot=self.bot,
                main_message_id=0,  # временно
                main_channel_id=channelId
            )
        )
        
        # Обновляем кнопку с правильным ID сообщения
        await message.edit(
            view=FormButton(
                applicant=applicant,
                bot=self.bot,
                main_message_id=message.id,
                main_channel_id=channelId
            )
        )
