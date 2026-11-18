# ============================================================
# Пчолки AI — бот тикетов
# Для Railway: токен берётся из переменной окружения DISCORD_TOKEN
# ============================================================

import os
import re
import json
import asyncio
import aiohttp
from datetime import datetime, timezone, timedelta
from pathlib import Path

import discord
from discord import ui
from discord.ext import commands

BASE = Path(__file__).resolve().parent

TOKEN = os.environ.get("DISCORD_TOKEN", "")
if not TOKEN:
    TOKEN_FILE = BASE / "ticket_token.txt"
    if TOKEN_FILE.exists():
        TOKEN = TOKEN_FILE.read_text(encoding="utf-8").strip()
if not TOKEN or "ВСТАВЬ" in TOKEN:
    raise RuntimeError(
        "Токен не найден! Добавь переменную окружения DISCORD_TOKEN на Railway."
    )

PANEL_CHANNEL    = os.environ.get("PANEL_CHANNEL", "create-ticket")
SUPPORT_CATEGORY = os.environ.get("SUPPORT_CATEGORY", "Support")
LOG_CHANNEL      = os.environ.get("LOG_CHANNEL", "ai-logs")
HELP_CHANNEL     = os.environ.get("HELP_CHANNEL", "ai-help")
OPENROUTER_KEY   = os.environ.get("OPENROUTER_API_KEY", "")
TICKETS_PNG      = BASE / "Tickets.png"
STAFF_ROLES = [
    "Assistant", "Mod", "*",
]

MSK = timezone(timedelta(hours=3))

DESCRIPTION = (
    "🇷🇺 Нужна помощь или роль User? Создайте тикет. "
    "Тикеты не по теме и от имени других людей запрещены.\n\n"
    "🇺🇸 Need help or the User role? Create a ticket. "
    "Off-topic tickets and tickets on behalf of others are not allowed."
)

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

ticket_meta: dict[int, dict] = {}
ticket_counter = 0

# ---------- Статистика ----------

STATS_FILE = BASE / "stats.json"

def load_stats() -> dict:
    if STATS_FILE.exists():
        try:
            return json.loads(STATS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"opened": 0, "closed": 0, "staff": {}}

def save_stats(stats: dict):
    STATS_FILE.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

stats = load_stats()


async def ask_ai(question: str) -> str:
    if not OPENROUTER_KEY:
        return "❌ OpenRouter API ключ не настроен."
    system_prompt = (
        "Ты — Пчолки AI, эксперт по Bee Swarm Simulator (Roblox). "
        "Пользователь написал тебе вопрос. СРАЗУ отвечай на него — без вступлений, без 'привет', без 'какой у тебя вопрос'. "
        "Просто дай ответ. На русском. С эмодзи."
    )
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        "max_tokens": 600,
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://discord.com",
        "X-Title": "Пчолки AI",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                data = await resp.json()
                if "choices" in data:
                    return data["choices"][0]["message"]["content"]
                elif "error" in data:
                    return f"❌ Ошибка API: {data['error'].get('message', str(data['error']))}"
                else:
                    return f"❌ Неожиданный ответ: {str(data)[:300]}"
    except Exception as e:
        return f"❌ Ошибка при запросе к AI: {e}"


# ---------- Логирование ----------

async def log_ticket(guild: discord.Guild, embed: discord.Embed):
    log_ch = discord.utils.get(guild.text_channels, name=LOG_CHANNEL)
    if log_ch:
        try:
            await log_ch.send(embed=embed)
        except discord.Forbidden:
            print(f"Нет прав писать в #{LOG_CHANNEL}")
    else:
        print(f"Канал #{LOG_CHANNEL} не найден.")


# ---------- Модалка закрытия ----------

class CloseModal(ui.Modal, title="Закрытие тикета"):
    reason = ui.TextInput(
        label="Причина закрытия / что сделано",
        placeholder="Опиши что было сделано или причину закрытия...",
        style=discord.TextStyle.paragraph,
        max_length=500,
    )

    def __init__(self, channel: discord.TextChannel, closer: discord.Member):
        super().__init__()
        self.ticket_channel = channel
        self.closer = closer

    async def on_submit(self, interaction: discord.Interaction):
        channel      = self.ticket_channel
        guild        = interaction.guild
        closer       = self.closer
        close_reason = str(self.reason)

        await interaction.response.send_message("Закрываю тикет...", ephemeral=True)

        meta        = ticket_meta.pop(channel.id, None)
        opener_name = meta["opener"]     if meta else "Неизвестно"
        opened_at   = meta["opened_at"]  if meta else "Неизвестно"
        category    = meta["category"]   if meta else "—"
        opener_id   = meta.get("opener_id") if meta else None

        # DM создателю тикета
        if opener_id:
            try:
                opener = await guild.fetch_member(opener_id)
                dm_embed = discord.Embed(
                    title="📪 Твой тикет закрыт",
                    color=discord.Color.orange(),
                    timestamp=datetime.now(MSK),
                )
                dm_embed.add_field(name="🗂️ Категория",       value=category,        inline=True)
                dm_embed.add_field(name="🔒 Закрыл",           value=str(closer),     inline=True)
                dm_embed.add_field(name="📝 Причина закрытия", value=close_reason,    inline=False)
                dm_embed.set_footer(text=f"Сервер: {guild.name}")
                await opener.send(embed=dm_embed)
                print(f"DM отправлен {opener}")
            except discord.NotFound:
                print(f"Участник {opener_id} не найден на сервере")
            except discord.Forbidden:
                print(f"Не удалось отправить DM — личные сообщения закрыты")

        # Лог в ai-logs
        log_embed = discord.Embed(
            title="📪 Тикет закрыт",
            color=discord.Color.red(),
            timestamp=datetime.now(MSK),
        )
        log_embed.add_field(name="🗂️ Категория",       value=category,                    inline=True)
        log_embed.add_field(name="🎟️ ID тикета",       value=f"`{channel.id}`",           inline=False)
        log_embed.add_field(name="👤 Открыл",           value=opener_name,                 inline=True)
        log_embed.add_field(name="🕐 Когда открыт",     value=opened_at,                   inline=True)
        log_embed.add_field(name="🔒 Закрыл",           value=f"{closer} (`{closer.id}`)", inline=False)
        log_embed.add_field(name="📝 Причина закрытия", value=close_reason,                inline=False)
        log_embed.set_footer(text="Пчолки AI • Ticket Log")
        await log_ticket(guild, log_embed)

        # Транскрипт
        transcript_lines = []
        async for msg in channel.history(limit=500, oldest_first=True):
            if msg.author == bot.user and not msg.content:
                continue  # пропускаем embed-сообщения бота
            ts = msg.created_at.astimezone(MSK).strftime("%d.%m.%Y %H:%M МСК")
            line = f"[{ts}] {msg.author}: {msg.content}"
            if msg.attachments:
                line += " " + " ".join(a.url for a in msg.attachments)
            transcript_lines.append(line)

        if transcript_lines:
            transcript_text = (
                f"Транскрипт тикета | {category} | Открыл: {opener_name} | {opened_at}\n"
                f"{'='*60}\n"
            ) + "\n".join(transcript_lines)
            transcript_bytes = transcript_text.encode("utf-8")
            transcript_file = discord.File(
                fp=__import__("io").BytesIO(transcript_bytes),
                filename=f"transcript-{channel.name}.txt",
            )
            log_ch = discord.utils.get(guild.text_channels, name=LOG_CHANNEL)
            if log_ch:
                await log_ch.send(
                    content=f"📋 Транскрипт тикета `{channel.name}`",
                    file=transcript_file,
                )

        # Статистика
        stats["closed"] += 1
        closer_key = str(closer)
        stats["staff"][closer_key] = stats["staff"].get(closer_key, 0) + 1
        save_stats(stats)

        try:
            await channel.delete()
        except discord.Forbidden:
            await interaction.followup.send("Не хватает прав на удаление канала.", ephemeral=True)


# ---------- Модалка открытия ----------

class TicketModal(ui.Modal):
    def __init__(self, category: str):
        super().__init__(title=f"Тикет — {category}")
        self.category = category
        self.reason = ui.TextInput(
            label="Опиши проблему",
            placeholder="Напиши кратко причину обращения...",
            style=discord.TextStyle.paragraph,
            max_length=500,
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        await create_ticket_channel(interaction, self.category, str(self.reason))


# ---------- Выбор категории ----------

class CategorySelect(ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @ui.select(
        placeholder="Выбери категорию...",
        custom_id="ticket_category_select",
        options=[
            discord.SelectOption(label="Помощь", emoji="🆘", description="Нужна помощь или роль User"),
            discord.SelectOption(label="Жалоба", emoji="⚠️", description="Пожаловаться на игрока"),
        ]
    )
    async def select_category(self, interaction: discord.Interaction, select: ui.Select):
        await interaction.response.send_modal(TicketModal(select.values[0]))


# ---------- Создание канала тикета ----------

async def create_ticket_channel(interaction: discord.Interaction, category_name: str, reason: str):
    global ticket_counter
    guild = interaction.guild
    user  = interaction.user

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

    ticket_counter += 1
    safe = re.sub(r"[^a-z0-9-]", "", user.name.lower())[:20] or "user"
    name = f"ticket-{safe}"

    try:
        channel = await guild.create_text_channel(
            name=name, category=category, topic=topic, overwrites=overwrites
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ Не хватает прав на создание каналов.", ephemeral=True
        )
        return

    opened_at = datetime.now(MSK).strftime("%d.%m.%Y %H:%M МСК")
    ticket_meta[channel.id] = {
        "opener":    f"{user} (`{user.id}`)",
        "opener_id": user.id,
        "opened_at": opened_at,
        "category":  category_name,
    }

    # Лог открытия
    log_embed = discord.Embed(
        title="📬 Тикет открыт",
        color=discord.Color.green(),
        timestamp=datetime.now(MSK),
    )
    log_embed.add_field(name="🗂️ Категория", value=category_name,               inline=True)
    log_embed.add_field(name="🎟️ ID тикета", value=f"`{channel.id}`",           inline=False)
    log_embed.add_field(name="👤 Открыл",     value=f"{user} (`{user.id}`)",     inline=True)
    log_embed.add_field(name="🕐 Когда",      value=opened_at,                   inline=True)
    log_embed.add_field(name="📝 Причина",    value=reason,                      inline=False)
    log_embed.add_field(name="📌 Канал",      value=channel.mention,             inline=False)
    log_embed.set_footer(text="Пчолки AI • Ticket Log")
    await log_ticket(guild, log_embed)

    # Статистика
    stats["opened"] += 1
    save_stats(stats)

    # Сообщение внутри тикета
    ticket_embed = discord.Embed(
        title=f"Тикет — {category_name}",
        color=discord.Color.blurple(),
    )
    ticket_embed.add_field(name="👤 Открыл",    value=user.mention,  inline=True)
    ticket_embed.add_field(name="🗂️ Категория", value=category_name, inline=True)
    ticket_embed.add_field(name="📝 Причина",   value=reason,        inline=False)
    ticket_embed.set_footer(text="Саппорт ответит здесь. Когда всё готово — нажми Close Ticket.")
    await channel.send(content=user.mention, embed=ticket_embed, view=CloseView())

    await interaction.response.send_message(
        f"✅ Тикет создан: {channel.mention}", ephemeral=True
    )
    print(f"Тикет создан для {user} [{category_name}]")


# ---------- Кнопки ----------

class CloseView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_ticket")
    async def close(self, interaction: discord.Interaction, button: ui.Button):
        channel = interaction.channel
        closer  = interaction.user

        user_role_names = [r.name for r in closer.roles]
        is_staff = any(r in user_role_names for r in STAFF_ROLES)

        if not is_staff:
            await interaction.response.send_message(
                "❌ Только персонал может закрывать тикеты.", ephemeral=True
            )
            return

        await interaction.response.send_modal(CloseModal(channel, closer))


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
        user  = interaction.user
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

        await interaction.response.send_message(
            "Выбери тип обращения:", view=CategorySelect(), ephemeral=True
        )


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
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if (
        isinstance(message.channel, discord.Thread)
        and message.channel.parent
        and message.channel.parent.name == HELP_CHANNEL
    ):
        async with message.channel.typing():
            answer = await ask_ai(message.content)
        embed = discord.Embed(description=answer, color=discord.Color.yellow())
        embed.set_footer(text="Пчолки AI • BSS Help")
        await message.reply(embed=embed)
    await bot.process_commands(message)


# ---------- Кнопка создания ветки в ai-help ----------

class CreateThreadView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(
        label="Создать ветку",
        style=discord.ButtonStyle.primary,
        emoji="🐝",
        custom_id="create_help_thread",
    )
    async def create_thread(self, interaction: discord.Interaction, button: ui.Button):
        channel = interaction.channel
        user = interaction.user
        thread_name = f"вопрос от {user.name}"
        try:
            thread = await channel.create_thread(
                name=thread_name,
                type=discord.ChannelType.public_thread,
                auto_archive_duration=1440,
            )
            await thread.send(
                content=user.mention,
                embed=discord.Embed(
                    description="🐝 Задавай вопрос по **Bee Swarm Simulator** — отвечу!",
                    color=discord.Color.yellow(),
                ).set_footer(text="Пчолки AI • BSS Help"),
            )
            await interaction.response.send_message(
                f"✅ Ветка создана: {thread.mention}", ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Нет прав создавать ветки.", ephemeral=True
            )


async def post_help_panel(channel: discord.TextChannel):
    embed = discord.Embed(
        title="🐝 Пчолки AI — помощник по Bee Swarm Simulator",
        description=(
            "Привет! Я Пчолки AI — твой помощник по **Bee Swarm Simulator**.\n\n"
            "Знаю всё про пчёл и их редкости, типы ульев и лучшие билды, "
            "баффы и стаки, поля для фарма, квесты медведей, промокоды и многое другое.\n\n"
            "Нажми кнопку ниже — создастся личная ветка где ты сможешь задать любой вопрос. "
            "Отвечаю быстро и по делу 🍯"
        ),
        color=discord.Color.yellow(),
    )
    embed.set_footer(text="Пчолки AI • BSS Help")
    await channel.send(embed=embed, view=CreateThreadView())
    print(f"Панель ai-help отправлена в #{channel.name}")


@bot.event
async def on_ready():
    print(f"Бот вошёл как {bot.user} (Пчолки AI)")
    try:
        await bot.tree.sync()
    except Exception as e:
        print("Не удалось синхронизовать команды:", e)

    channel = discord.utils.get(bot.get_all_channels(), name=PANEL_CHANNEL)
    if channel is None:
        print(f"Канал #{PANEL_CHANNEL} не найден.")
        return

    bot.add_view(TicketView())
    bot.add_view(CloseView())
    bot.add_view(CreateThreadView())

    # Панель ai-help
    help_channel = discord.utils.get(bot.get_all_channels(), name=HELP_CHANNEL)
    if help_channel:
        # Удаляем старую панель
        async for msg in help_channel.history(limit=20):
            if msg.author == bot.user:
                try:
                    await msg.delete()
                except discord.Forbidden:
                    pass
        await post_help_panel(help_channel)
    else:
        print(f"Канал #{HELP_CHANNEL} не найден.")

    bot_add_view = CreateThreadView()
    bot.add_view(bot_add_view)
    async for msg in channel.history(limit=50):
        if msg.author == bot.user:
            try:
                await msg.delete()
                print("Старая панель удалена.")
            except discord.Forbidden:
                print("Нет прав удалить старую панель.")
    await post_panel(channel)


@bot.tree.command(name="stats", description="Статистика тикетов")
async def ticket_stats(interaction: discord.Interaction):
    # Только стафф
    user_role_names = [r.name for r in interaction.user.roles]
    is_staff = any(r in user_role_names for r in STAFF_ROLES)
    if not is_staff:
        await interaction.response.send_message("❌ Нет доступа.", ephemeral=True)
        return

    currently_open = len(ticket_meta)

    embed = discord.Embed(
        title="📊 Статистика тикетов",
        color=discord.Color.blurple(),
        timestamp=datetime.now(MSK),
    )
    embed.add_field(name="📬 Открыто всего",    value=str(stats["opened"]),  inline=True)
    embed.add_field(name="📪 Закрыто всего",    value=str(stats["closed"]),  inline=True)
    embed.add_field(name="🟢 Сейчас открытых", value=str(currently_open),   inline=True)

    if stats["staff"]:
        top = sorted(stats["staff"].items(), key=lambda x: x[1], reverse=True)[:5]
        top_text = "\n".join(f"`{i+1}.` {name} — **{count}** закрыт." for i, (name, count) in enumerate(top))
        embed.add_field(name="🏆 Топ стаффа", value=top_text, inline=False)

    embed.set_footer(text="Пчолки AI • Stats")
    await interaction.response.send_message(embed=embed)


bot.run(TOKEN)
