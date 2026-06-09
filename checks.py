import discord
from datetime import datetime, timedelta

def check_account_age(user: discord.Member) -> tuple:
    account_age = datetime.now(user.created_at.tzinfo) - user.created_at
    days_old = account_age.days
    
    if days_old < 30:
        return False, days_old, f"❌ Ваш аккаунт создан менее месяца назад."
    else:
        return True, days_old, f"✅ Возраст аккаунта: {days_old} дней"