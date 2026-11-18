# ============================================================
# Пчолки AI — бот тикетов
# Для Railway: токен берётся из переменной окружения DISCORD_TOKEN
# ============================================================

import os
import re
from pathlib import Path

import discord
from discord import ui
from discord.ext import commands

BASE = Path(__file__).resolve().parent

# Токен из переменной окружения (Railway) или из файла для локалки
TOKEN = os.environ.get("DISCORD_TOKEN", "")
if not TOKEN:
    TOKEN_FILE = BASE / "ticket_token.txt"
    if TOKEN_FILE.exists():
        TOKEN = TOKEN_FILE.read_text(encoding="utf-8").strip()
if not TOKEN or "ВСТАВЬ" in TOKEN:
    raise RuntimeError(
        "Токен не найден! Добавь переменную окружения DISCORD_TOKEN на Railway."
    )

PANEL_CHANNEL = os.environ.get("PANEL_CHANNEL", "create-ticket")
SUPPORT_CATEGORY = os.environ.get("SUPPORT_CATEGORY", "Support")
TICKETS_PNG = BASE / "Tickets.png"
STAFF_ROLES = [
    "Staff", "Support", "Администратор", "Admin", "Moderator", "Модератор", "Админ",
]

DESCRIPTION = (
    "🇷🇺 Нужна помощь или роль User? Создайте тикет. "
    "Тикеты не по теме и от имени других людей запрещены.\n\n"
    "🇺🇸 Need help or the User role? Create a ticket. "
    "Off-topic tickets and tickets on behalf of others are not allowed."
)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


# ---------- Кнопки ----------

class CloseView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_ticket")
    async def close(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("Закрываю тикет...", ephemeral=True)
        try:
            await interaction.channel.delete()
        except discord.Forbidden:
            await interaction.followup.send("Не хватает прав на удаление канала.", ephemeral=True)


class TicketView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(
        label="Create Ticket",
        style=discord.ButtonStyle.success,
        emoji="🎟️",
        custom_id="create_ticket",
        row=0,
    )
    async def create_ticket(self, interaction: discord.Interaction, button: ui.Button):
        guild = interaction.guild
        user = interaction.user
        if guild is None:
            return

        topic = f"ticket:{user.id}"
        existing = next(
            (ch for ch in guild.text_channels if ch.topic == topic), None
        )
        if existing:
            await interaction.response.send_message(
                f"У тебя уже есть открытый тикет: {existing.mention}", ephemeral=True
            )
            return

        category = discord.utils.get(guild.categories, name=SUPPORT_CATEGORY)
        if category is None:
            category = await guild.create_category(SUPPORT_CATEGORY)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
            ),
        }
        for role_name in STAFF_ROLES:
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                )

        safe = re.sub(r"[^a-z0-9-]", "", user.name.lower())[:20] or "user"
        name = f"ticket-{safe}"

        try:
            channel = await guild.create_text_channel(
                name=name, category=category, topic=topic, overwrites=overwrites
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Не хватает прав на создание каналов. "
                "Перепригласи бота с правом **Manage Channels**.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="Тикет создан 🎫",
            description=(
                f"{user.mention}, опиши свою проблему и приложи скриншоты.\n\n"
                "Саппорт ответит здесь. Когда всё готово — нажми **Close Ticket**."
            ),
            color=discord.Color.blurple(),
        )
        await channel.send(content=user.mention, embed=embed, view=CloseView())

        await interaction.response.send_message(
            f"✅ Тикет создан: {channel.mention}", ephemeral=True
        )
        print(f"Тикет создан: {channel.name} для {user}")


# ---------- Панель ----------

def build_panel() -> tuple[discord.Embed, TicketView]:
    embed = discord.Embed(description=DESCRIPTION, color=discord.Color.blurple())
    embed.set_image(url="attachment://Tickets.png")
    return embed, TicketView()


async def post_panel(channel: discord.TextChannel):
    embed, view = build_panel()
    file = discord.File(TICKETS_PNG, filename="Tickets.png")
    await channel.send(embed=embed, view=view, file=file)
    print(f"Панель тикетов отправлена в #{channel.name}")


# ---------- События ----------

@bot.event
async def on_ready():
    print(f"Бот вошёл как {bot.user} (Пчолки AI)")
    try:
        await bot.tree.sync()
    except Exception as e:
        print("Не удалось синхронизовать команды:", e)

    channel = discord.utils.get(bot.get_all_channels(), name=PANEL_CHANNEL)
    if channel is None:
        print(f"Канал #{PANEL_CHANNEL} не найден. Создай его или поменяй переменную PANEL_CHANNEL.")
        return

    need_post = True
    async for msg in channel.history(limit=20):
        if msg.author == bot.user and msg.embeds:
            ids = [
                getattr(c, "custom_id", None)
                for row in msg.components
                for c in row.children
            ]
            has_image = bool(msg.embeds[0].image)
            if "create_ticket" in ids and has_image:
                print("Панель уже актуальна — пропускаю.")
                need_post = False
                break
            try:
                await msg.delete()
                print("Старая панель удалена.")
            except discord.Forbidden:
                print("Нет прав удалить старую панель.")
    if need_post:
        await post_panel(channel)


@bot.tree.command(name="setup_tickets", description="Опубликовать панель тикетов")
async def setup_tickets(interaction: discord.Interaction):
    await post_panel(interaction.channel)
    await interaction.response.send_message("Готово!", ephemeral=True)


bot.run(TOKEN)
