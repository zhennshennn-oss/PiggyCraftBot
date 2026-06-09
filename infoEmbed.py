import discord
from discord.ui import View, Button
from formEmbed import SurveyModal
from checks import check_account_age

class ApplicationButton(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        
        self.apply_button = Button(
            label="Подать заявку",
            emoji="✉️",
            style = discord.ButtonStyle.green,
            custom_id="apply_botton"
        ) 
        
        self.buy_button = Button(
            label="Купить проходку",
            emoji="💵",
            style=discord.ButtonStyle.url,
            url = "https://piggycraft.cdonate.ru/",
        )
        
        self.apply_button.callback = self.button_callback
        self.buy_button.callback = self.button_callback
        self.add_item(self.apply_button)
        self.add_item(self.buy_button)
        
    async def button_callback(self, interaction: discord.Interaction):
        is_old_enough, days, message = check_account_age(interaction.user)
        
        if not is_old_enough:
            embed = discord.Embed(
                title="⛔ Доступ запрещён",
                description=message + "\n\nПопробуйте позже или купите платную проходку.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        modal = SurveyModal(bot=self.bot)
        await interaction.response.send_modal(modal)

def infoEmbed():
    piggycraftText1 = "PiggyCraft — ванильный Minecraft-сервер, созданный для тех, кто ценит честное и спокойное выживание без гриферства, хаоса и анархии. Здесь каждый шаг строится на доверии, уважении и желании вместе развивать мир, в котором каждый игрок может вложить частичку себя в общее приключение."
    piggycraftText4 = "Чтобы играть на сервере, необходимо подать заявку на **бесплатную** проходку или купить **платную**, если вам отказали или не хотите ждать ответа администрации"
    rule1 = "• Анкета будет рассматриваться в течении 24 часов;"
    rule2 = "• Вы обязаны быть активным, адекватным и грамотным;"
    rule3 = "• В заполнении анкеты стоит быть честным и подробным, это увеличит шансы одобрения;"
    rule4 = "• Заявка не будет рассматриваться, если ваш аккаунт создан менее месяца назад"
    rule5 = "• Вы будете оповещены о статусе заявки"
    
    embed = discord.Embed(
        color = 0x242429,
        image = "https://i.pinimg.com/1200x/24/b4/a1/24b4a1a3db937ab7254575f70922a103.jpg",
        description=(
            f"## Что такое Piggycraft?  \n{piggycraftText1}\n\n"
            f"## Как начать играть?\n{piggycraftText4}\n\n"
            f"## Что важно знать?\n {rule1}\n {rule2}\n {rule3}\n {rule4}\n {rule5}"
        )
    )
    return embed
