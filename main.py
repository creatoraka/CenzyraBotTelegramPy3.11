import os
import re
import random
import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.enums import ParseMode, ChatType, ChatPermissions
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# ==================== КОНФИГ ====================

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Не задана переменная окружения BOT_TOKEN")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

TEMP_BANS = {}
TEMP_MUTES = {}
RPS_GAMES = {}
CENSOR_ENABLED = {}
USERNAME_CACHE = {}
SERVICE_CLEANER_ENABLED = {}

# ==================== НОРМАЛИЗАЦИЯ ====================

HOMOGLYPHS = str.maketrans({
    "a": "а", "e": "е", "o": "о", "p": "р", "c": "с",
    "x": "х", "y": "у", "k": "к", "m": "м", "t": "т",
    "h": "н", "b": "в", "n": "п",
    "0": "о", "1": "и", "3": "з", "4": "а", "6": "б", "8": "в", "9": "д",
})

NOT_LETTERS = re.compile(r"[^а-я]")


def normalize(text: str) -> str:
    """Lower, гомоглифы→рус, только буквы, сжимаем все повторы."""
    if not text:
        return ""
    text = text.lower()
    text = text.replace("ё", "е")
    text = text.translate(HOMOGLYPHS)
    text = NOT_LETTERS.sub("", text)
    text = re.sub(r"(.)\1+", r"\1", text)
    return text


# ==================== МАТ-КОРНИ ====================

MAT_ROOTS = [
    # хуй
    "хуй", "хуя", "хую", "хуе", "хуи", "хул",
    "хуесос", "хуеплет", "хуеглот", "хуемраз",
    # хер
    "хер",
    # пизд
    "пизд", "пизж",
    # бля
    "бляд", "блят", "бля",
    # еб
    "еб", "ебан", "ебал", "ебат", "ебу", "еби", "ебло",
    "заеб", "наеб", "отъеб", "подъеб", "уеб", "въеб",
    "проеб", "разъеб", "съеб", "доеб", "долбоеб",
    "перееб", "поеб", "недоеб",
    # сук
    "сука", "суки", "суке", "суку", "сукой", "сучар", "сучк", "суч",
    "засук",
    # муд
    "мудак", "мудил", "мудор", "мудозвон", "мудень", "мудня",
    # гандон
    "гандон", "гондон", "ганд",
    # пидор
    "пидор", "пидар", "пидер", "пидр", "педик", "педер", "педераст",
    "пидорас", "пидарас",
    # гомик
    "гомик", "гомосек",
    # залуп
    "залуп",
    # манда
    "манда", "мандав",
    # шлюх
    "шлюх", "шлюш",
    # проститут
    "проститут",
    # шалав
    "шалав", "потаск", "хабал", "стерв", "курв", "блуд",
    # физиология
    "влагалищ", "вагин", "клитор", "сперм",
    # срак
    "срак", "срать", "срал", "срач",
    # сса
    "ссат", "ссал", "ссан", "ссик",
    # перд
    "перд", "бзд",
    # говн
    "говн", "дерьм", "какашк", "жоп", "задниц",
    # анал
    "анал", "анус",
    # дроч
    "дроч", "онанизм", "онанист", "мастурб",
    # минет
    "минет", "миньет", "кунилингус", "фелл", "фелляц", "орал",
    # секс
    "секс", "сексуаль",
    # трах
    "трах",
    # шмар
    "шмар",
    # национальные
    "хохол", "хохлы", "москал", "кацап", "жид", "чурка", "чурки",
    "чурбан", "чучмек", "хачик", "хачи", "азерб", "армяшк", "дагест",
    "чечен", "узбек", "китаез", "немчура",
    # фаш/наци
    "фашист", "нацист", "гитлер", "рашист", "рашизм", "ватник",
    # наркота
    "героин", "герыч", "кокаин", "амфетамин", "мефедрон", "метамфетамин",
    "марихуан", "гашиш", "мескалин", "экстази", "закладк", "закладчик",
    "наркота", "наркотик", "наркоман", "торчок",
    # суицид
    "суицид", "самоубий", "повесит", "повешусь", "убить", "убийств",
    "зарежу", "вскрытвен",
    # терроризм
    "террорист", "терроризм", "теракт", "взорвать", "джихад", "шахид",
    "смертник", "игилов", "алькаид", "талиб",
    # педофилия
    "педофил", "малолетк", "малолеток", "несовершеннолетн",
    # оскорбления
    "сволоч", "мразь", "мрази", "мразот", "тварь", "твари", "тварюг",
    "ублюдок", "ублюдки", "кретин", "кретинк", "дебил", "дебильн",
    "идиот", "идиотк", "придурок", "придурки", "урод", "уроды", "уродств",
    "гнида", "гниды", "падла", "падлы", "падлюка", "дрянь", "дряни",
    "мерзавец", "мерзавк", "негодяй", "подлец", "поганец", "хамло",
    "нахалюга", "дегенерат", "олигофрен", "дауненок", "аутист",
    # угрозы
    "убью", "прикончить", "уничтож", "порву", "порвать", "сожгу",
    "сжечь", "казн", "казнить", "расправ", "размажу", "раздавлю",
    "сломаю", "сломать", "изобью", "избить",
    "изнасил", "изнасилую", "изнасиловать",
]

_seen = set()
MAT_ROOTS_UNIQ = []
for r in MAT_ROOTS:
    if r not in _seen:
        _seen.add(r)
        MAT_ROOTS_UNIQ.append(r)

# Сортируем от длинных к коротким — важно для корректного re.search
MAT_ROOTS_UNIQ.sort(key=len, reverse=True)

MAT_PATTERN = re.compile("|".join(re.escape(r) for r in MAT_ROOTS_UNIQ))

# Whitelist — точные слова, которые не мат
WHITELIST_RAW = {
    "херсон", "херсонес", "херсонский",
    "мандарин", "мандарины", "мандаринка", "мандариновый", "мандаринчик",
    "анализ", "анализа", "аналитик", "аналитика", "анализировать",
    "трахея", "трахеит", "трахеи", "трахеотомия",
    "секстант", "секстанта",
    "сукаленок", "сукаленка",
    "сракозябра", "сракозябры",
    "моченый", "моченая", "моченые",
    "оральный", "оральная", "оральное",
    "половой", "половая", "половое", "половые",
    "половинка", "половина", "половину",
    "сношение", "сношения",
    "дешевка", "дешевки", "дешевле",
    "соль", "соли", "солью",
    "фаллос", "фаллоса",
    "пенис", "пениса",
    "вагина", "вагины", "вагинальный",
    "клитор", "клитора",
    "анальный", "анальная", "анальное",
    "сексуальный", "сексуальная", "сексуальное", "сексуальность",
    "мастурбация",
    "наркотик", "наркотики",
    "хамство", "хамства",
    "поганец",
}

WHITELIST = {normalize(w) for w in WHITELIST_RAW}


def has_bad_words(text: str) -> bool:
    """
    Проверка мата:
    1) по словам — каждое нормализуем, ищем мат-корень
    2) по склеенному тексту — ловим 'б л я т ь'
    Whitelist исключается на всех уровнях.
    """
    if not text:
        return False

    # 1) по словам
    words = re.findall(r"[A-Za-zА-Яа-яЁё0-9]+", text)
    for w in words:
        wn = normalize(w)
        if not wn:
            continue
        if wn in WHITELIST:
            continue
        if MAT_PATTERN.search(wn):
            return True

    # 2) склеенный текст
    flat = normalize(text)
    if flat and flat not in WHITELIST:
        if MAT_PATTERN.search(flat):
            return True

    return False


# ==================== МАГИЧЕСКИЙ ШАР ====================

MAGIC_8_BALL = [
    "🎱 Да, однозначно.", "🎱 Нет, даже не думай.", "🎱 Возможно.",
    "🎱 Спроси позже.", "🎱 Не могу сказать сейчас.", "🎱 Абсолютно точно.",
    "🎱 Скорее нет, чем да.", "🎱 Скорее да, чем нет.",
    "🎱 Не рассчитывай на это.", "🎱 Все звёзды за.",
    "🎱 Мои источники говорят «нет».", "🎱 Определённо да.",
    "🎱 Сомневаюсь.", "🎱 Знаки говорят «да».",
    "🎱 Туманно, попробуй ещё раз.", "🎱 Да, но осторожно.",
    "🎱 Лучше не спрашивай.", "🎱 Всё возможно в этом мире.",
    "🎱 Судьба решит за тебя.", "🎱 Я бы на твоём месте подумал.",
]

# ==================== СЕРВИСНЫЕ СООБЩЕНИЯ ====================

SERVICE_PATTERNS = [
    re.compile(r".+\s+пригласил[а]?\s+.+", re.IGNORECASE),
    re.compile(r".+\s+invited\s+.+", re.IGNORECASE),
    re.compile(r".+\s+добавил[а]?\s+.+", re.IGNORECASE),
    re.compile(r".+\s+added\s+.+", re.IGNORECASE),
    re.compile(r".+\s+вступил[а]?\s+(в|к)\s+", re.IGNORECASE),
    re.compile(r".+\s+присоединил(ся|ась)\s+", re.IGNORECASE),
    re.compile(r".+\s+joined\s+(the\s+)?group", re.IGNORECASE),
    re.compile(r".+\s+вышел\s+из\s+", re.IGNORECASE),
    re.compile(r".+\s+вышла\s+из\s+", re.IGNORECASE),
    re.compile(r".+\s+покинул[а]?\s+", re.IGNORECASE),
    re.compile(r".+\s+left\s+(the\s+)?group", re.IGNORECASE),
    re.compile(r".+\s+удалил[а]?\s+.+", re.IGNORECASE),
    re.compile(r".+\s+removed\s+.+", re.IGNORECASE),
    re.compile(r".+\s+изменил[а]?\s+название", re.IGNORECASE),
    re.compile(r"^(закрепл[её]нн?[оы][ем]?\s+сообщение|pinned\s+message)", re.IGNORECASE),
]


def is_service_message(message: types.Message) -> bool:
    if message.new_chat_members:
        return True
    if message.left_chat_member:
        return True
    for attr in (
        "new_chat_title", "new_chat_photo", "delete_chat_photo",
        "pinned_message", "group_chat_created", "supergroup_chat_created",
        "channel_chat_created", "migrate_to_chat_id", "migrate_from_chat_id",
        "video_chat_started", "video_chat_ended", "video_chat_scheduled",
        "video_chat_participants_invited", "proximity_alert_triggered",
        "forum_topic_created", "forum_topic_closed", "forum_topic_reopened",
    ):
        if getattr(message, attr, None):
            return True

    text = message.text or message.caption or ""
    if text and len(text) <= 200:
        for pattern in SERVICE_PATTERNS:
            if pattern.search(text):
                if "@" in text or text[0].isupper():
                    return True

    return False


def service_cleaner_enabled(chat_id: int) -> bool:
    return SERVICE_CLEANER_ENABLED.get(chat_id, True)


# ==================== КЭШ ПОЛЬЗОВАТЕЛЕЙ ====================

def cache_user(chat_id: int, user: types.User):
    if not user or not user.username:
        return
    USERNAME_CACHE.setdefault(chat_id, {})[user.username.lower()] = user.id


def resolve_username(chat_id: int, username: str):
    if not username:
        return None
    return USERNAME_CACHE.get(chat_id, {}).get(username.lstrip("@").lower())


def extract_username_from_text(text: str):
    if not text:
        return None
    m = re.search(r"@([A-Za-z0-9_]{4,32})", text)
    return m.group(0) if m else None


def extract_user_id_from_text(text: str):
    if not text:
        return None
    m = re.search(r"\b(\d{6,15})\b", text)
    return int(m.group(1)) if m else None


async def resolve_target(message: types.Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        u = message.reply_to_message.from_user
        cache_user(message.chat.id, u)
        return u.id, u.full_name, None

    text = message.text or ""

    if message.entities:
        for entity in message.entities:
            if entity.type == "text_mention" and entity.user:
                u = entity.user
                cache_user(message.chat.id, u)
                return u.id, u.full_name, None
            if entity.type == "mention":
                username = text[entity.offset:entity.offset + entity.length]
                uid = resolve_username(message.chat.id, username)
                if uid:
                    return uid, username, None
                return None, username, (
                    "❌ Не удалось определить ID по @username.\n"
                    "Пользователь ни разу не писал в этом чате.\n"
                    "Используй reply или укажи числовой ID."
                )

    username = extract_username_from_text(text)
    if username:
        uid = resolve_username(message.chat.id, username)
        if uid:
            return uid, username, None
        return None, username, (
            f"❌ Не удалось найти <code>{username}</code> в кэше чата.\n"
            "Пользователь должен хоть раз написать сообщение."
        )

    uid = extract_user_id_from_text(text)
    if uid:
        return uid, f"ID {uid}", None

    return None, None, (
        "❌ Укажи пользователя:\n"
        "• ответь (reply) на его сообщение\n"
        "• укажи @username (если он писал в чате)\n"
        "• укажи числовой ID"
    )


def extract_target_user(message: types.Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        u = message.reply_to_message.from_user
        return u.id, u.full_name
    text = message.text or ""
    if message.entities:
        for entity in message.entities:
            if entity.type == "text_mention" and entity.user:
                u = entity.user
                return u.id, u.full_name
            if entity.type == "mention":
                username = text[entity.offset:entity.offset + entity.length]
                uid = resolve_username(message.chat.id, username)
                if uid:
                    return uid, username
                return None, username
    username = extract_username_from_text(text)
    if username:
        uid = resolve_username(message.chat.id, username)
        if uid:
            return uid, username
        return None, username
    return None, None


# ==================== УТИЛИТЫ ====================

async def is_admin(message: types.Message) -> bool:
    if message.chat.type == ChatType.PRIVATE:
        return True
    try:
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        return member.status in ("administrator", "creator")
    except Exception as e:
        logging.warning(f"is_admin: {e}")
        return False


async def is_target_admin(message: types.Message, target_id: int) -> bool:
    if message.chat.type == ChatType.PRIVATE:
        return False
    try:
        member = await bot.get_chat_member(message.chat.id, target_id)
        return member.status in ("administrator", "creator")
    except Exception as e:
        logging.warning(f"is_target_admin: {e}")
        return False


async def is_target_bot(message: types.Message, target_id: int) -> bool:
    try:
        me = await bot.get_me()
        return target_id == me.id
    except Exception:
        return False


async def bot_can_restrict(message: types.Message) -> bool:
    try:
        me = await bot.get_me()
        member = await bot.get_chat_member(message.chat.id, me.id)
        return bool(getattr(member, "can_restrict_members", False))
    except Exception as e:
        logging.warning(f"bot_can_restrict: {e}")
        return False


async def bot_can_delete(message: types.Message) -> bool:
    if message.chat.type == ChatType.PRIVATE:
        return False
    try:
        me = await bot.get_me()
        member = await bot.get_chat_member(message.chat.id, me.id)
        return bool(getattr(member, "can_delete_messages", False))
    except Exception as e:
        logging.warning(f"bot_can_delete: {e}")
        return False


def parse_minutes(args):
    for a in args[1:]:
        if a.isdigit() and len(a) <= 5:
            n = int(a)
            if n > 0:
                return n
    return None


async def check_target(message: types.Message, user_id: int, name: str) -> bool:
    if await is_target_bot(message, user_id):
        await message.reply("🤖 Нельзя наказывать самого бота.")
        return False
    if await is_target_admin(message, user_id):
        await message.reply(f"🛡 <b>{name}</b> — админ/владелец чата. Его нельзя наказать.")
        return False
    return True


# ==================== КОМАНДЫ ====================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    cache_user(message.chat.id, message.from_user)
    await message.answer(
        "👋 Привет! Я бот-цензор.\n\n"
        "🛡 Удаляю мат автоматически\n"
        "🧹 Чищу сервисные сообщения\n"
        "🎲 Развлекательные команды\n"
        "🔨 Модерация\n\n"
        "📌 /help для списка команд."
    )


@dp.message(Command("help"))
@dp.message(Command("помощь"))
async def cmd_help(message: types.Message):
    await message.answer(
        "🛡 <b>Бот-цензор</b>\n\n"
        "<b>🎲 Развлечения:</b>\n"
        "/rps — КНБ с ботом или @user\n"
        "/dice — кубик\n"
        "/coin — орёл/решка\n"
        "/ball &lt;вопрос&gt; — магический шар\n\n"
        "<b>🔨 Модерация (для админов):</b>\n"
        "/delete — удалить сообщение (reply)\n"
        "/kick — кикнуть (@user или reply)\n"
        "/ban — забанить (@user или reply)\n"
        "/unban — разбанить (@user или ID)\n"
        "/tempban &lt;мин&gt; — временный бан\n"
        "/mute &lt;мин&gt; — мут\n"
        "/unmute — снять мут\n\n"
        "<b>🛡 Управление (для админов):</b>\n"
        "/censor — включить цензуру\n"
        "/uncensor — выключить цензуру\n"
        "/censor_status — статус цензуры\n"
        "/service_on — вкл. чистку сервисных\n"
        "/service_off — выкл. чистку\n"
        "/service_status — статус чистки"
    )


@dp.message(Command("censor"))
@dp.message(Command("цензура"))
async def cmd_censor_on(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        await message.answer("❌ Только в группах.")
        return
    if not await is_admin(message):
        await message.reply("❌ Только админы.")
        return
    CENSOR_ENABLED[message.chat.id] = True
    await message.answer("✅ Цензура <b>включена</b>.")


@dp.message(Command("uncensor"))
@dp.message(Command("безцензуры"))
async def cmd_censor_off(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        await message.answer("❌ Только в группах.")
        return
    if not await is_admin(message):
        await message.reply("❌ Только админы.")
        return
    CENSOR_ENABLED[message.chat.id] = False
    await message.answer("🔓 Цензура <b>выключена</b>.")


@dp.message(Command("censor_status"))
@dp.message(Command("статусцензуры"))
async def cmd_censor_status(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        await message.answer("❌ Только в группах.")
        return
    status = CENSOR_ENABLED.get(message.chat.id, True)
    emoji = "✅" if status else "🔓"
    state = "включена" if status else "выключена"
    await message.answer(f"{emoji} Цензура <b>{state}</b>.")


@dp.message(Command("service_on"))
async def cmd_service_on(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        await message.answer("❌ Только в группах.")
        return
    if not await is_admin(message):
        await message.reply("❌ Только админы.")
        return
    SERVICE_CLEANER_ENABLED[message.chat.id] = True
    await message.answer("✅ Чистка сервисных <b>включена</b>.")


@dp.message(Command("service_off"))
async def cmd_service_off(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        await message.answer("❌ Только в группах.")
        return
    if not await is_admin(message):
        await message.reply("❌ Только админы.")
        return
    SERVICE_CLEANER_ENABLED[message.chat.id] = False
    await message.answer("🔓 Чистка сервисных <b>выключена</b>.")


@dp.message(Command("service_status"))
async def cmd_service_status(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        await message.answer("❌ Только в группах.")
        return
    status = SERVICE_CLEANER_ENABLED.get(message.chat.id, True)
    emoji = "✅" if status else "🔓"
    state = "включена" if status else "выключена"
    await message.answer(f"{emoji} Чистка сервисных <b>{state}</b>.")


# ==================== /delete ====================

@dp.message(Command("delete"))
@dp.message(Command("удалить"))
async def cmd_delete(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        await message.answer("❌ Только в группах.")
        return
    if not await is_admin(message):
        try:
            await message.delete()
        except Exception:
            pass
        return
    if not await bot_can_delete(message):
        await message.reply("❌ Нет прав на удаление.")
        return
    if not message.reply_to_message:
        try:
            await message.delete()
        except Exception:
            pass
        return

    target_id = message.reply_to_message.message_id
    try:
        await bot.delete_message(message.chat.id, target_id)
    except Exception as e:
        logging.warning(f"delete target: {e}")
    try:
        await message.delete()
    except Exception as e:
        logging.warning(f"delete command: {e}")


# ==================== КНБ ====================

RPS_CHOICES = {
    "rock": "✊ Камень",
    "scissors": "✌️ Ножницы",
    "paper": "✋ Бумага",
}
RPS_BEATS = {"rock": "scissors", "scissors": "paper", "paper": "rock"}


def rps_result(a: str, b: str) -> str:
    if a == b:
        return "draw"
    if RPS_BEATS[a] == b:
        return "a"
    return "b"


def rps_keyboard(game_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✊ Камень", callback_data=f"rps:{game_id}:rock"),
        InlineKeyboardButton(text="✌️ Ножницы", callback_data=f"rps:{game_id}:scissors"),
        InlineKeyboardButton(text="✋ Бумага", callback_data=f"rps:{game_id}:paper"),
    ]])


def make_game_id(chat_id: int, user_id: int) -> str:
    return f"{chat_id}_{user_id}_{random.randint(100000, 999999)}"


@dp.message(Command("rps"))
@dp.message(Command("кнб"))
async def cmd_rps(message: types.Message):
    target_id, target_name = extract_target_user(message)

    if target_id is None and target_name:
        await message.reply(
            f"❌ Не удалось найти <code>{target_name}</code> в кэше чата.\n"
            "Ответь (reply) на его сообщение и напиши /rps."
        )
        return

    if target_id is None:
        game_id = make_game_id(message.chat.id, message.from_user.id)
        bot_choice_key = random.choice(list(RPS_CHOICES.keys()))
        RPS_GAMES[game_id] = {
            "player_a": message.from_user.id,
            "player_b": None,
            "choice_a": None,
            "choice_b": bot_choice_key,
            "is_bot": True,
            "a_name": message.from_user.full_name,
            "a_mention": message.from_user.mention_html(),
            "b_name": "🤖 Бот",
            "b_mention": "🤖 Бот",
            "chat_id": message.chat.id,
        }
        await message.answer(
            "🎮 <b>КНБ с ботом</b>\n\n"
            f"👤 {message.from_user.mention_html()}, твой ход:",
            reply_markup=rps_keyboard(game_id)
        )
        return

    if target_id == message.from_user.id:
        await message.reply("❌ Нельзя играть с самим собой.")
        return

    me = await bot.get_me()
    if target_id == me.id:
        await message.reply("🤖 Чтобы сыграть со мной, напиши просто /rps без аргументов.")
        return

    game_id = make_game_id(message.chat.id, message.from_user.id)
    target_mention = f'<a href="tg://user?id={target_id}">{target_name}</a>'

    RPS_GAMES[game_id] = {
        "player_a": message.from_user.id,
        "player_b": target_id,
        "choice_a": None,
        "choice_b": None,
        "is_bot": False,
        "a_name": message.from_user.full_name,
        "a_mention": message.from_user.mention_html(),
        "b_name": target_name,
        "b_mention": target_mention,
        "chat_id": message.chat.id,
    }

    await message.answer(
        f"🎮 <b>Вызов на КНБ!</b>\n\n"
        f"🥊 {message.from_user.mention_html()} vs {target_mention}\n\n"
        f"👉 <b>{message.from_user.full_name}</b>, выбери свой ход первым:",
        reply_markup=rps_keyboard(game_id)
    )


@dp.callback_query(F.data.startswith("rps:"))
async def rps_callback(call: CallbackQuery):
    parts = call.data.split(":")
    if len(parts) != 3:
        await call.answer("Некорректный вызов.", show_alert=True)
        return

    _, game_id, choice = parts
    game = RPS_GAMES.get(game_id)
    if not game:
        await call.answer("Игра не найдена или завершена.", show_alert=True)
        return

    user_id = call.from_user.id

    if game["is_bot"]:
        if user_id != game["player_a"]:
            await call.answer("Эта игра не твоя.", show_alert=True)
            return
        player_choice = choice
        bot_choice = game["choice_b"]
        result = rps_result(player_choice, bot_choice)
        if result == "draw":
            verdict = "🤝 Ничья!"
        elif result == "a":
            verdict = f"🎉 Победил {game['a_name']}!"
        else:
            verdict = "😢 Победил бот!"
        try:
            await call.message.edit_text(
                f"🎮 <b>КНБ с ботом</b>\n\n"
                f"👤 {game['a_mention']}: {RPS_CHOICES[player_choice]}\n"
                f"🤖 Бот: {RPS_CHOICES[bot_choice]}\n\n"
                f"<b>{verdict}</b>"
            )
        except Exception:
            pass
        await call.answer()
        RPS_GAMES.pop(game_id, None)
        return

    if user_id == game["player_a"]:
        slot = "a"
    elif user_id == game["player_b"]:
        slot = "b"
    else:
        await call.answer("Ты не участник этой игры.", show_alert=True)
        return

    if game.get(f"choice_{slot}") is not None:
        await call.answer("Ты уже сделал выбор!", show_alert=True)
        return

    game[f"choice_{slot}"] = choice
    await call.answer(f"Ты выбрал: {RPS_CHOICES[choice]}")

    if game["choice_a"] is not None and game["choice_b"] is not None:
        ca, cb = game["choice_a"], game["choice_b"]
        result = rps_result(ca, cb)
        if result == "draw":
            verdict = "🤝 Ничья!"
        elif result == "a":
            verdict = f"🏆 Победил {game['a_mention']}!"
        else:
            verdict = f"🏆 Победил {game['b_mention']}!"
        text = (
            f"🎮 <b>КНБ — результат</b>\n\n"
            f"👤 {game['a_mention']}: {RPS_CHOICES[ca]}\n"
            f"👤 {game['b_mention']}: {RPS_CHOICES[cb]}\n\n"
            f"<b>{verdict}</b>"
        )
        try:
            await call.message.edit_text(text)
        except Exception:
            await call.message.answer(text)
        RPS_GAMES.pop(game_id, None)
        return

    next_name = game["b_mention"] if game["choice_a"] is not None else game["a_mention"]
    try:
        await call.message.edit_text(
            f"🎮 <b>КНБ</b>\n\n"
            f"🥊 {game['a_mention']} vs {game['b_mention']}\n\n"
            f"👉 Теперь ход: {next_name}",
            reply_markup=rps_keyboard(game_id)
        )
    except Exception:
        pass


# ==================== РАЗВЛЕКАТЕЛЬНЫЕ ====================

@dp.message(Command("dice"))
@dp.message(Command("кубик"))
async def cmd_dice(message: types.Message):
    value = random.randint(1, 6)
    await message.answer(f"🎲 Выпало: <b>{value}</b>")


@dp.message(Command("coin"))
@dp.message(Command("монетка"))
async def cmd_coin(message: types.Message):
    result = random.choice(["🪙 Орёл", "🪙 Решка"])
    await message.answer(f"Подбрасываю... <b>{result}</b>")


@dp.message(Command("ball"))
@dp.message(Command("шар"))
async def cmd_ball(message: types.Message):
    text = message.text or ""
    parts = text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer("🔮 Задай вопрос: <code>/ball Я стану миллионером?</code>")
        return
    question = parts[1].strip()
    answer = random.choice(MAGIC_8_BALL)
    await message.answer(f"❓ <i>{question}</i>\n\n{answer}")


# ==================== МОДЕРАЦИЯ ====================

@dp.message(Command("kick"))
@dp.message(Command("кик"))
async def cmd_kick(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ Только админы.")
        return
    if not await bot_can_restrict(message):
        await message.reply("❌ Нет прав на ограничение.")
        return
    user_id, name, err = await resolve_target(message)
    if err:
        await message.reply(err)
        return
    if not await check_target(message, user_id, name):
        return
    try:
        await bot.ban_chat_member(message.chat.id, user_id)
        await bot.unban_chat_member(message.chat.id, user_id)
        await message.answer(f"👢 {name} кикнут.")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")


@dp.message(Command("ban"))
@dp.message(Command("бан"))
async def cmd_ban(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ Только админы.")
        return
    if not await bot_can_restrict(message):
        await message.reply("❌ Нет прав на ограничение.")
        return
    user_id, name, err = await resolve_target(message)
    if err:
        await message.reply(err)
        return
    if not await check_target(message, user_id, name):
        return
    try:
        await bot.ban_chat_member(message.chat.id, user_id)
        await message.answer(f"🔨 {name} забанен навсегда.")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")


@dp.message(Command("unban"))
@dp.message(Command("разбан"))
async def cmd_unban(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ Только админы.")
        return
    if not await bot_can_restrict(message):
        await message.reply("❌ Нет прав на ограничение.")
        return
    user_id, name, err = await resolve_target(message)
    if err:
        await message.reply(err)
        return
    try:
        await bot.unban_chat_member(message.chat.id, user_id, only_if_banned=True)
        await message.answer(f"🔓 {name} разбанен.")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")


@dp.message(Command("tempban"))
@dp.message(Command("врембан"))
async def cmd_tempban(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ Только админы.")
        return
    if not await bot_can_restrict(message):
        await message.reply("❌ Нет прав на ограничение.")
        return
    user_id, name, err = await resolve_target(message)
    if err:
        await message.reply(err)
        return
    if not await check_target(message, user_id, name):
        return
    args = (message.text or "").split()
    minutes = parse_minutes(args)
    if not minutes:
        await message.reply("❌ Укажи время: <code>/tempban 30</code>")
        return
    try:
        until_ts = int((datetime.now() + timedelta(minutes=minutes)).timestamp())
        await bot.ban_chat_member(message.chat.id, user_id, until_date=until_ts)
        TEMP_BANS.setdefault(message.chat.id, {})[user_id] = (
            datetime.now() + timedelta(minutes=minutes)
        )
        await message.answer(f"⏱ {name} забанен на <b>{minutes} мин.</b>")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")


@dp.message(Command("mute"))
@dp.message(Command("мут"))
async def cmd_mute(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ Только админы.")
        return
    if not await bot_can_restrict(message):
        await message.reply("❌ Нет прав на ограничение.")
        return
    user_id, name, err = await resolve_target(message)
    if err:
        await message.reply(err)
        return
    if not await check_target(message, user_id, name):
        return
    args = (message.text or "").split()
    minutes = parse_minutes(args)
    if not minutes:
        await message.reply("❌ Укажи время: <code>/mute 15</code>")
        return
    try:
        until_ts = int((datetime.now() + timedelta(minutes=minutes)).timestamp())
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=user_id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_ts
        )
        TEMP_MUTES.setdefault(message.chat.id, {})[user_id] = (
            datetime.now() + timedelta(minutes=minutes)
        )
        await message.answer(f"🔇 {name} замучен на <b>{minutes} мин.</b>")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")


@dp.message(Command("unmute"))
@dp.message(Command("размут"))
async def cmd_unmute(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ Только админы.")
        return
    user_id, name, err = await resolve_target(message)
    if err:
        await message.reply(err)
        return
    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_change_info=False,
                can_invite_users=True,
                can_pin_messages=False,
            )
        )
        TEMP_MUTES.get(message.chat.id, {}).pop(user_id, None)
        await message.answer(f"🔊 {name} размучен.")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")


# ==================== АВТОУДАЛЕНИЕ СЕРВИСНЫХ ====================

@dp.message(F.new_chat_members)
async def on_new_chat_members(message: types.Message):
    if not service_cleaner_enabled(message.chat.id):
        return
    try:
        await message.delete()
        logging.info(f"Удалено сервисное (new_chat_members) в {message.chat.id}")
    except Exception as e:
        logging.warning(f"Не удалось удалить сервисное: {e}")


@dp.message(F.left_chat_member)
async def on_left_chat_member(message: types.Message):
    if not service_cleaner_enabled(message.chat.id):
        return
    try:
        await message.delete()
        logging.info(f"Удалено сервисное (left_chat_member) в {message.chat.id}")
    except Exception as e:
        logging.warning(f"Не удалось удалить сервисное: {e}")


@dp.message(F.pinned_message)
async def on_pinned_message(message: types.Message):
    if not service_cleaner_enabled(message.chat.id):
        return
    try:
        await message.delete()
        logging.info(f"Удалено сервисное (pinned_message) в {message.chat.id}")
    except Exception as e:
        logging.warning(f"Не удалось удалить сервисное: {e}")


@dp.message(F.new_chat_title | F.new_chat_photo | F.delete_chat_photo)
async def on_chat_changes(message: types.Message):
    if not service_cleaner_enabled(message.chat.id):
        return
    try:
        await message.delete()
        logging.info(f"Удалено сервисное (chat_changes) в {message.chat.id}")
    except Exception as e:
        logging.warning(f"Не удалось удалить сервисное: {e}")


# ==================== ОБЩИЙ ФИЛЬТР ====================

@dp.message()
async def filter_messages(message: types.Message):
    # Кэшируем авторов
    if message.from_user:
        cache_user(message.chat.id, message.from_user)
    if message.reply_to_message and message.reply_to_message.from_user:
        cache_user(message.chat.id, message.reply_to_message.from_user)

    # Сервисные по тексту
    if service_cleaner_enabled(message.chat.id) and is_service_message(message):
        try:
            await message.delete()
            logging.info(f"Удалено сервисное (text) в {message.chat.id}")
        except Exception as e:
            logging.warning(f"Не удалось удалить сервисное: {e}")
        return

    if not message.text:
        return
    if message.text.startswith("/"):
        return
    if not CENSOR_ENABLED.get(message.chat.id, True):
        return

    if has_bad_words(message.text):
        try:
            await message.delete()
            logging.info(
                f"Удалено сообщение от {message.from_user.id} "
                f"в чате {message.chat.id}"
            )
        except Exception as e:
            logging.warning(f"Не удалось удалить сообщение: {e}")


# ==================== РЕГИСТРАЦИЯ КОМАНД ====================

async def set_commands():
    commands = [
        types.BotCommand(command="start", description="Запустить бота"),
        types.BotCommand(command="help", description="Все команды бота"),
        types.BotCommand(command="rps", description="КНБ с ботом или @user"),
        types.BotCommand(command="dice", description="Бросить кубик"),
        types.BotCommand(command="coin", description="Орёл или решка"),
        types.BotCommand(command="ball", description="Магический шар"),
        types.BotCommand(command="delete", description="Удалить сообщение (reply)"),
        types.BotCommand(command="censor", description="Включить цензуру"),
        types.BotCommand(command="uncensor", description="Выключить цензуру"),
        types.BotCommand(command="censor_status", description="Статус цензуры"),
        types.BotCommand(command="service_on", description="Вкл. чистку сервисных"),
        types.BotCommand(command="service_off", description="Выкл. чистку сервисных"),
        types.BotCommand(command="service_status", description="Статус чистки"),
        types.BotCommand(command="kick", description="Кикнуть (@user или reply)"),
        types.BotCommand(command="ban", description="Забанить (@user или reply)"),
        types.BotCommand(command="unban", description="Разбанить (@user/ID/reply)"),
        types.BotCommand(command="tempban", description="Врембан (@user или reply)"),
        types.BotCommand(command="mute", description="Мут (@user или reply)"),
        types.BotCommand(command="unmute", description="Снять мут (@user или reply)"),
    ]
    try:
        await bot.set_my_commands(commands)
    except Exception as e:
        logging.warning(f"set_my_commands: {e}")


# ==================== ЗАПУСК ====================

async def main():
    await asyncio.sleep(5)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        logging.warning(f"delete_webhook: {e}")

    await set_commands()
    logging.info("Бот-цензор запущен...")

    while True:
        try:
            await dp.start_polling(bot)
            break
        except Exception as e:
            logging.error(f"Polling упал: {e}. Повтор через 10 сек...")
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
