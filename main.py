import os
import re
import random
import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode, ChatType
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery,
    BusinessConnection, ChatPermissions
)

# ==================== КОНФИГ ====================

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Не задана переменная окружения BOT_TOKEN")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

print("=== START BOT ===")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# ==================== СУПЕР-АДМИНЫ ====================

SUPER_ADMINS = {"creatoraka"}
SUPER_ADMIN_IDS = set()

# ==================== ХРАНИЛИЩА ====================

TEMP_BANS = {}
TEMP_MUTES = {}
RPS_GAMES = {}
RPS_INVITES = {}
RPS_REMATCH = {}          # {rematch_id: {"players": set(), "clicked": set(), "chat_id": ..., "a_id": ..., "b_id": ..., "a_name": ..., "b_name": ...}}
CENSOR_ENABLED = {}
CAPS_ENABLED = {}
LINKS_ENABLED = {}
USERNAME_CACHE = {}
USER_ID_TO_NAME = {}
WARMED_CHATS = set()
SERVICE_CLEANER_ENABLED = {}

USER_STATS = {}
BUSINESS_CONNECTIONS = {}
BOT_ID = None

# ==================== НОРМАЛИЗАЦИЯ ====================

HOMOGLYPHS = str.maketrans({
    "a": "а", "e": "е", "o": "о", "p": "р", "c": "с",
    "x": "х", "y": "у", "k": "к", "m": "м", "t": "т",
    "h": "н", "b": "в", "n": "п",
    "0": "о", "1": "и", "3": "з", "4": "а", "6": "б", "8": "в", "9": "д",
})

NOT_LETTERS = re.compile(r"[^а-я]")


def normalize(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = text.replace("ё", "е")
    text = text.translate(HOMOGLYPHS)
    text = NOT_LETTERS.sub("", text)
    return text


# ==================== МАТ ====================

LONG_BAD = [
    "хуесос", "хуеплет", "хуеглот", "хуемраз",
    "пизда", "пизде", "пизду", "пизды", "пиздо",
    "пиздец", "пиздану", "пиздато", "пиздатый",
    "пиздюк", "пиздюл", "пиздюх",
    "пиздобол", "пиздабол", "пиздоболка",
    "пиздрик", "пиздрила", "пиздренок",
    "пиздюлина", "пиздюлей", "пиздюли",
    "распизд", "запизд", "впизд", "спизд", "испизд",
    "напизд", "пропизд", "припизд", "допизд",
    "блядина", "блядинк", "блядищ",
    "блядство", "блядств", "блядск", "блядская",
    "блядун", "блядуш",
    "блядва", "блядво",
    "забляд", "набляд", "пробляд",
    "выбляд", "выблядок",
    "добляд", "прибляд",
    "ебан", "ебану", "ебанут", "ебанул",
    "ебат", "ебать", "ебал",
    "ебало", "ебальник",
    "ебарь", "ебари",
    "ебуч", "ебучий",
    "ебет", "ебется",
    "ебить", "ебитв", "ебитва",
    "ебля", "ебли",
    "ебло", "еблом",
    "еблан", "ебланк",
    "ебств", "ебусь", "ебут",
    "ебака",
    "заеб", "заебал", "заебись", "заебу", "заебан",
    "наеб", "наебал", "наебать", "наебут", "наебан", "наебка",
    "отъеб", "отъебал", "отъебать", "отъебис", "отъебись",
    "подъеб", "подъебал", "подъебка", "подъебну",
    "уебал", "уебать", "уебан", "уебищ",
    "въеб", "въебал", "въебать", "въебну",
    "проеб", "проебал", "проебать", "проебан", "проебу",
    "разъеб", "разъебал", "разъебать", "разъебан",
    "съеб", "съебал", "съебать", "съебался", "съебись",
    "доебал", "доебать", "доебис", "доебись",
    "долбоеб", "долбаеб", "долбоебка",
    "недоеб",
    "перееб", "переебал", "переебать", "переебан", "переебу",
    "поебал", "поебать", "поебен", "поебень", "поебон",
    "поебушка", "поебух", "ебалда",
    "сучка", "сучки", "сучонок",
    "сучара", "сучарк", "сучий", "сучья",
    "мудак", "мудачь",
    "мудил", "мудила", "мудило",
    "мудозвон",
    "мудень", "мудня",
    "замуд", "намуд", "промуда",
    "пидор", "пидар", "пидер",
    "педик", "педер", "педераст",
    "пидорас", "пидарас", "пидорасина",
    "пидорств", "пидарств",
    "пидорок",
    "гандон", "гондон",
    "кондом",
    "паскуд", "паскудник",
    "падлюк", "падлюка", "падлючк",
    "гомик", "гомосек",
    "залупка", "залупок",
    "мандавошк", "мандав", "мандуй",
    "шлюха", "шлюхи", "шлюхо", "шлюхе", "шлюху",
    "шлюшка", "шлюшки", "шлюшк", "шлюшонок", "шлюшня",
    "пошлюх",
    "проститут", "проститух",
    "шалава", "шалавы", "шалавищ",
    "потаскух", "потаскушк",
    "хабалка", "хабалк",
    "влагалищ",
    "спермат", "сперматозо", "сперматозоид",
    "мошонк", "мошонка",
    "срака", "сраку", "сраки",
    "срать", "срала",
    "срача", "сраче",
    "ссать", "ссала", "ссанин",
    "пердеж", "пердану", "пердун", "пердунь",
    "бздеж", "бздун",
    "говно", "говна", "говне", "говну",
    "говнюк", "говнюшк",
    "говня", "говнян", "говняст",
    "дерьм", "дерьмо", "дерьма",
    "мочалк",
    "фекал", "фекали",
    "испражн",
    "экскремен",
    "жопа", "жопу", "жопе", "жопы",
    "жопан", "жопень",
    "задниц", "задница", "задницу",
    "анальн",
    "простат", "простата",
    "дрочи", "дрочил", "дрочить", "дрочер",
    "онанизм", "онанист",
    "мастурб", "мастурбац", "мастурби",
    "минет", "миньет", "минетч",
    "кунилингус", "кунилинг",
    "фелляц",
    "сексуаль", "сексуальн",
    "половойакт",
    "совокуп", "совокуплен",
    "трахат", "трахаю", "трахал", "трахать", "трахнул",
    "шмара", "шмары",
    "дешевка",
    "хохол", "хохлы", "хохлушк",
    "москаль", "москаля",
    "кацапн",
    "жидяр",
    "чурбан",
    "чучмек",
    "хачик",
    "армяшк", "армяшка",
    "дагест", "дагестан",
    "чечен", "чеченец",
    "китаез", "китаеза",
    "немчура",
    "фашист", "нацист",
    "гитлер",
    "рашист", "рашизм",
    "ватник",
    "героин", "герыч",
    "кокаин",
    "амфетамин",
    "мефедрон",
    "метамфетамин",
    "марихуан",
    "гашиш",
    "мескалин",
    "экстази",
    "закладк", "закладчик",
    "наркота", "наркотик",
    "наркоман", "наркоманк",
    "торчок",
    "ширнут", "ширнул",
    "суицид",
    "самоубий", "самоубийств",
    "повесит", "повешусь", "повесил",
    "убийств", "убийц",
    "зарежу",
    "вскрытвен",
    "террорист", "терроризм", "теракт",
    "взорвать",
    "джихад",
    "шахид",
    "смертник",
    "игилов",
    "алькаид",
    "талиб",
    "педофил",
    "малолетк", "малолеток",
    "несовершеннолетн",
    "сволочь", "сволочи",
    "мразь", "мрази", "мразот",
    "тварь", "твари", "тварюг",
    "ублюдок", "ублюдки",
    "кретин", "кретинк",
    "дебильн",
    "идиот", "идиотк",
    "придурок", "придурки",
    "уродств",
    "гнида", "гниды",
    "падлюка",
    "мерзавец", "мерзавк",
    "негодяй",
    "поганец",
    "хамло",
    "нахалюга",
    "дегенерат",
    "олигофрен",
    "дауненок",
    "аутист",
    "изнасил", "изнасилую", "изнасиловать",
]

SHORT_BAD = [
    "хуй", "хуя", "хую", "хуе", "хуи", "хуйн",
    "хуйло", "хуйня", "хуец", "хуищ", "хуяч", "хуяр",
    "хуел", "хуею", "хуев",
    "схуя", "схуй",
    "нахуй", "похуй", "нахуя", "похуя", "нахуе", "похуе",
    "нахую", "похую", "нахуи", "похуи",
    "хер",
    "пизд", "пизж",
    "блядь", "бляди", "блядо", "бляде", "бляду",
    "блять", "блят", "бляд", "бля",
    "еб", "ебу", "еби",
    "сука", "суки", "суке", "суку", "сукой", "сучар", "сучк",
    "суч", "засук",
    "мудор",
    "ганд",
    "пидр",
    "гомо",
    "манда", "манде", "манду", "манды", "мандо",
    "шлюх", "шлюш",
    "шлюха", "шлюхи", "шлюхе", "шлюху", "шлюхой",
    "шалав", "потаск", "хабал", "стерв",
    "курв", "курва", "курвы", "курво",
    "блуд",
    "вагин", "вагина",
    "сперм", "сперма",
    "яичк",
    "срак",
    "сру", "срал",
    "срач", "срачь",
    "ссат", "ссал", "ссан", "ссани",
    "ссик", "ссику",
    "перд", "пердну", "бзд",
    "вонюч",
    "моча", "мочит", "мочен",
    "жоп",
    "анал",
    "анус",
    "дроч",
    "онан",
    "фелл",
    "орал",
    "секс", "секса", "сексу", "сексе",
    "снош",
    "трах", "трахн",
    "шмар",
    "кацап", "жид",
    "чурка", "чурки", "чурк",
    "хач", "хачи",
    "азерб", "узбек", "немч", "наци",
    "нарк", "нарко", "торч",
    "бомб", "бомба", "игил",
    "педо",
    "мраз", "твар",
    "урод", "уроды", "уродина",
    "дрян", "дрянь", "дрянн",
    "подлец",
    "поган",
    "хам", "хамл", "хамск",
    "наглец", "нагл",
    "нахал", "наха",
    "залупа", "залупе", "залупу", "залупы", "залупой",
    "убью",
    "порву", "порвать",
    "сожгу", "сжечь",
]

WHITELIST_RAW = {
    "херсон", "херсонес", "херсонский", "херсонская", "херсонский",
    "мандарин", "мандарины", "мандаринка", "мандаринка",
    "мандариновый", "мандаринчик", "мандаринчики",
    "анализ", "анализа", "анализу", "анализом", "анализе",
    "аналитик", "аналитика", "аналитики", "аналитику",
    "анализировать", "анализировал", "анализирую",
    "аналог", "аналога", "аналогия", "аналогичный", "аналогично",
    "аналоговый",
    "трахея", "трахеи", "трахею", "трахеей", "трахеит",
    "трахеотомия", "трахеостомия",
    "секстант", "секстанта", "секстанты",
    "секция", "секции", "секцию", "секций", "секционный",
    "секрет", "секрета", "секретный", "секретно",
    "секретарь", "секретариат",
    "сукаленок", "сукаленка",
    "сукно", "сукна", "сукном", "сукне",
    "суккулент", "суккуленты",
    "сукровица",
    "сракозябра", "сракозябры",
    "половой", "половая", "половое", "половые", "половых",
    "половинка", "половина", "половину", "половины",
    "половник", "половники",
    "оральный", "оральная", "оральное", "оральные",
    "орал", "орала", "орали", "орать",
    "сношение", "сношения", "сношению", "сношением",
    "сносно", "сносный", "сносная", "сносное", "сносные",
    "сноска", "сноски", "сноску",
    "дешевка", "дешевки", "дешевке", "дешевку", "дешевкой",
    "дешевле", "дешевый", "дешевая", "дешево",
    "соль", "соли", "солью",
    "соленый", "соленая", "соленое",
    "солнечный", "солнечная", "солнце",
    "анальный", "анальная", "анальное", "анальные",
    "вагина", "вагины", "вагине", "вагину", "вагиной",
    "вагинальный", "вагинальная",
    "клитор", "клитора", "клиторе", "клитору", "клитором",
    "клиторальный",
    "фаллос", "фаллоса", "фаллосу", "фаллосом",
    "пенис", "пениса", "пенису", "пенисом",
    "пенистый", "пенистая",
    "сексуальный", "сексуальная", "сексуальное", "сексуальные",
    "сексуальность", "сексуально",
    "мастурбация", "мастурбации", "мастурбацию",
    "наркотик", "наркотики", "наркотика", "наркотиков",
    "наркоз", "наркоза", "наркозный",
    "хамство", "хамства", "хамству", "хамством",
    "поганец", "поганка", "поганки",
    "поганый", "поганая", "поганое", "поганые",
    "трава", "травы", "траве", "траву", "травой", "травам", "травах",
    "травинка", "травинки", "травинку",
    "травля", "травли", "травлю",
    "травма", "травмы", "травме", "травму", "травмой",
    "травматолог", "травматология",
    "траверс", "траверса",
    "лупа", "лупы", "лупе", "лупу", "лупой",
    "лупить", "луплю", "лупит",
    "муравей", "муравья", "муравью", "муравьи", "муравьёв", "муравьев",
    "муравьиный", "муравьиная", "муравейник", "муравейника",
    "суккулент", "суккуленты", "суккулентный",
}

WHITELIST = {normalize(w) for w in WHITELIST_RAW}


def has_bad_words(text: str) -> bool:
    if not text:
        return False

    raw_words = re.findall(r"[A-Za-zА-Яа-яЁё0-9]+", text)
    norm_words = [normalize(w) for w in raw_words if normalize(w)]

    if not norm_words:
        return False

    # Одно слово из whitelist — пропускаем
    if len(norm_words) == 1 and norm_words[0] in WHITELIST:
        return False

    # Проверка по словам
    for w in norm_words:
        if w in WHITELIST:
            continue
        for bad in LONG_BAD:
            if bad in w:
                return True

    for w in norm_words:
        if w in WHITELIST:
            continue
        if w in SHORT_BAD:
            return True
        for bad in SHORT_BAD:
            if len(bad) >= 3 and bad in w:
                return True

    # Только если нет пробелов (одно «слово» / склеено) — проверяем слитный текст
    if " " not in text.strip():
        flat = normalize(text)
        if flat and flat not in WHITELIST:
            for bad in SHORT_BAD:
                if len(bad) >= 3 and bad in flat:
                    return True
            for bad in LONG_BAD:
                if bad in flat:
                    return True

    return False


# ==================== КАПСЛОК ====================

def is_caps_lock(text: str, min_len: int = 6, threshold: float = 0.7) -> bool:
    if not text:
        return False
    letters = [c for c in text if c.isalpha()]
    if len(letters) < min_len:
        return False
    upper = sum(1 for c in letters if c.isupper())
    return (upper / len(letters)) >= threshold


# ==================== ССЫЛКИ ====================

URL_RE = re.compile(
    r"(?:https?://|www\.)[^\s<>\"']+",
    re.IGNORECASE
)

ALLOWED_LINK_PREFIXES = (
    "https://www.youtube.com/shorts",
    "http://www.youtube.com/shorts",
    "https://youtube.com/shorts",
    "http://youtube.com/shorts",
    "www.youtube.com/shorts",
    "youtube.com/shorts",
)


def is_allowed_link(url: str) -> bool:
    url_low = url.lower().rstrip("/")
    for prefix in ALLOWED_LINK_PREFIXES:
        if url_low.startswith(prefix):
            return True
    return False


def has_forbidden_links(text: str) -> bool:
    if not text:
        return False
    found = URL_RE.findall(text)
    for url in found:
        if not is_allowed_link(url):
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
]


def is_service_message(message: types.Message) -> bool:
    if message.new_chat_members is not None:
        return True
    if message.left_chat_member is not None:
        return True
    for attr in (
        "new_chat_title", "new_chat_photo", "delete_chat_photo",
        "pinned_message", "group_chat_created", "supergroup_chat_created",
        "channel_chat_created", "migrate_to_chat_id", "migrate_from_chat_id",
        "video_chat_started", "video_chat_ended", "video_chat_scheduled",
        "video_chat_participants_invited", "proximity_alert_triggered",
        "forum_topic_created", "forum_topic_closed", "forum_topic_reopened",
    ):
        if getattr(message, attr, None) is not None:
            return True

    text = message.text or message.caption or ""
    if text and len(text) <= 200:
        for pattern in SERVICE_PATTERNS:
            if pattern.search(text):
                if "@" in text or text[0].isupper():
                    return True

    return False


# ==================== КЭШ ПОЛЬЗОВАТЕЛЕЙ ====================

def cache_user(chat_id: int, user: types.User):
    if not user:
        return
    if user.username:
        USERNAME_CACHE.setdefault(chat_id, {})[user.username.lower()] = user.id
    USER_ID_TO_NAME[(chat_id, user.id)] = user.full_name


def track_message(chat_id: int, user: types.User, is_bad: bool = False):
    if not user or user.is_bot:
        return
    stats = USER_STATS.setdefault(chat_id, {})
    now = datetime.now()

    if user.id not in stats:
        stats[user.id] = {
            "messages": 0,
            "bad_words": 0,
            "first_seen": now,
            "last_seen": now,
            "name": user.full_name,
            "username": user.username or "",
        }

    entry = stats[user.id]
    entry["messages"] += 1
    if is_bad:
        entry["bad_words"] += 1
    entry["last_seen"] = now
    entry["name"] = user.full_name
    entry["username"] = user.username or entry["username"]


async def warm_cache(chat_id: int):
    if chat_id in WARMED_CHATS:
        return
    WARMED_CHATS.add(chat_id)
    try:
        admins = await bot.get_chat_administrators(chat_id)
        for admin in admins:
            if not admin.user.is_bot:
                cache_user(chat_id, admin.user)
    except Exception as e:
        print(f"warm_cache({chat_id}): {e}")


def resolve_username(chat_id: int, username: str):
    if not username:
        return None
    uname = username.lstrip("@").lower()
    return USERNAME_CACHE.get(chat_id, {}).get(uname)


def get_name(chat_id: int, user_id: int) -> str:
    return USER_ID_TO_NAME.get((chat_id, user_id), f"ID {user_id}")


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
    chat_id = message.chat.id

    if message.reply_to_message and message.reply_to_message.from_user:
        u = message.reply_to_message.from_user
        cache_user(chat_id, u)
        return u.id, u.full_name, None

    text = message.text or ""

    if message.entities:
        for entity in message.entities:
            if entity.type == "text_mention" and entity.user:
                u = entity.user
                cache_user(chat_id, u)
                return u.id, u.full_name, None
            if entity.type == "mention":
                username = text[entity.offset:entity.offset + entity.length]
                uid = resolve_username(chat_id, username)
                if uid:
                    return uid, get_name(chat_id, uid), None
                return None, username, (
                    f"❌ Не удалось найти <code>{username}</code>.\n"
                    "Пользователь должен хоть раз написать в этом чате.\n"
                    "Проверь кэш: /users\n"
                    "Или используй reply / числовой ID."
                )

    username = extract_username_from_text(text)
    if username:
        uid = resolve_username(chat_id, username)
        if uid:
            return uid, get_name(chat_id, uid), None
        return None, username, (
            f"❌ Не удалось найти <code>{username}</code> в кэше.\n"
            "Проверь кэш: /users\n"
            "Или используй reply / числовой ID."
        )

    uid = extract_user_id_from_text(text)
    if uid:
        return uid, f"ID {uid}", None

    return None, None, (
        "❌ Укажи пользователя:\n"
        "• ответь (reply) на его сообщение\n"
        "• укажи @username (см. /users)\n"
        "• укажи числовой ID"
    )


# ==================== ПРОВЕРКА ПРАВ ====================

def is_super_admin(message: types.Message) -> bool:
    if not message.from_user:
        return False
    uname = (message.from_user.username or "").lower()
    uid = message.from_user.id

    if uname and uname in SUPER_ADMINS:
        return True
    if uid in SUPER_ADMIN_IDS:
        return True
    return False


async def is_admin(message: types.Message) -> bool:
    if message.chat.type == ChatType.PRIVATE:
        return True
    if is_super_admin(message):
        return True
    try:
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        return member.status in ("administrator", "creator")
    except Exception as e:
        print(f"is_admin: {e}")
        return False


async def is_target_admin(message: types.Message, target_id: int) -> bool:
    if message.chat.type == ChatType.PRIVATE:
        return False
    try:
        member = await bot.get_chat_member(message.chat.id, target_id)
        return member.status in ("administrator", "creator")
    except Exception as e:
        print(f"is_target_admin: {e}")
        return False


async def bot_can_restrict(message: types.Message) -> bool:
    try:
        me = await bot.get_me()
        member = await bot.get_chat_member(message.chat.id, me.id)
        return bool(getattr(member, "can_restrict_members", False))
    except Exception as e:
        print(f"bot_can_restrict: {e}")
        return False


async def bot_can_promote(message: types.Message) -> bool:
    try:
        me = await bot.get_me()
        member = await bot.get_chat_member(message.chat.id, me.id)
        return bool(getattr(member, "can_promote_members", False))
    except Exception as e:
        print(f"bot_can_promote: {e}")
        return False


def parse_minutes(args):
    for a in args[1:]:
        if a.isdigit() and len(a) <= 5:
            n = int(a)
            if n > 0:
                return n
    return None


async def check_target(message: types.Message, user_id: int, name: str) -> bool:
    if user_id == BOT_ID:
        await message.reply("🤖 Нельзя наказывать самого бота.")
        return False

    for uname, cached_id in USERNAME_CACHE.get(message.chat.id, {}).items():
        if cached_id == user_id and uname in SUPER_ADMINS:
            await message.reply(
                f"🛡 <b>{name}</b> — супер-админ. Его нельзя наказать."
            )
            return False
    if user_id in SUPER_ADMIN_IDS:
        await message.reply(
            f"🛡 <b>{name}</b> — супер-админ. Его нельзя наказать."
        )
        return False

    if await is_target_admin(message, user_id):
        await message.reply(f"🛡 <b>{name}</b> — админ. Его нельзя наказать.")
        return False
    return True


# ==================== СТАТИСТИКА ====================

def human_delta(dt: datetime) -> str:
    delta = datetime.now() - dt
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return f"{seconds} сек. назад"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} мин. назад"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} ч. назад"
    days = hours // 24
    if days < 30:
        return f"{days} дн. назад"
    months = days // 30
    if months < 12:
        return f"{months} мес. назад"
    years = days // 365
    return f"{years} г. назад"


def human_date(dt: datetime) -> str:
    return dt.strftime("%d.%m.%Y %H:%M")


async def build_stats_message(message: types.Message, target_id, target_name):
    chat_id = message.chat.id

    if target_id is None:
        target_id = message.from_user.id
        target_name = message.from_user.full_name

    display_name = get_name(chat_id, target_id) if target_id else (target_name or "—")
    if target_id == message.from_user.id:
        display_name = message.from_user.full_name

    stats = USER_STATS.get(chat_id, {}).get(target_id)
    if not stats:
        return (
            f"👤 <b>{display_name}</b>\n\n"
            "📊 Нет данных — этот пользователь ещё не писал в чате "
            "(статистика ведётся с момента запуска бота)."
        )

    username_line = f"🔗 @{stats['username']}" if stats["username"] else ""
    total = stats["messages"]
    bad = stats["bad_words"]
    clean = total - bad

    text = (
        f"👤 <b>{stats['name']}</b>\n"
        f"{username_line}\n"
        f"🆔 <code>{target_id}</code>\n\n"
        f"📊 <b>Статистика в этом чате:</b>\n"
        f"• Всего сообщений: <b>{total}</b>\n"
        f"• Чистых: <b>{clean}</b>\n"
        f"• Нарушений (мат): <b>{bad}</b>\n\n"
        f"🕐 Первое сообщение: {human_date(stats['first_seen'])}\n"
        f"   ({human_delta(stats['first_seen'])})\n"
        f"🕐 Последнее: {human_delta(stats['last_seen'])}"
    )
    return text


@dp.message(Command("актив"))
@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        await message.answer(await build_stats_message(message, None, None))
        return

    user_id, name, err = await resolve_target(message)
    if err and not message.reply_to_message:
        args = (message.text or "").split()
        if len(args) < 2:
            user_id, name, err = None, None, None

    if err:
        await message.reply(err)
        return

    await message.answer(await build_stats_message(message, user_id, name))


@dp.message(Command("whoareyou"))
@dp.message(Command("ктоты"))
async def cmd_whoareyou(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        await message.answer(await build_stats_message(message, None, None))
        return

    user_id, name, err = await resolve_target(message)
    if err and not message.reply_to_message:
        args = (message.text or "").split()
        if len(args) < 2:
            user_id, name, err = None, None, None

    if err:
        await message.reply(err)
        return

    await message.answer(await build_stats_message(message, user_id, name))


# ==================== BUSINESS ====================

BUSINESS_HELP_TEXT = (
    "💼 <b>Business-бот — команды в личке</b>\n\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "<b>Мут собеседника</b>\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "• <code>.мут</code> — удалять все сообщения собеседника\n"
    "• Кнопка «🔊 Размутить» — снять мут\n\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "<b>Прочее</b>\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "• <code>.хелп</code> или <code>.help</code> — этот список\n\n"
    "⚠️ <i>Для мута нужно право «Удалять сообщения» в "
    "Настройках Telegram Business → Чат-боты.</i>"
)


@dp.business_connection()
async def on_business_connection(conn: BusinessConnection):
    print(
        f"\n=== BUSINESS CONNECTION ===\n"
        f"id={conn.id}\n"
        f"user_id={conn.user.id}\n"
        f"enabled={conn.is_enabled}\n"
        f"can_reply={getattr(conn, 'can_reply', None)}\n"
        f"can_delete_all_messages={getattr(conn, 'can_delete_all_messages', None)}\n"
    )

    if conn.is_enabled:
        BUSINESS_CONNECTIONS[conn.id] = {
            "owner_id": conn.user.id,
            "muted": set(),
            "can_delete": bool(getattr(conn, "can_delete_all_messages", False)),
        }
    else:
        BUSINESS_CONNECTIONS.pop(conn.id, None)


async def get_business_conn(conn_id: str):
    conn = BUSINESS_CONNECTIONS.get(conn_id)
    if conn:
        try:
            bc = await bot.get_business_connection(conn_id)
            conn["can_delete"] = bool(
                getattr(bc, "can_delete_all_messages", False)
            )
            conn["owner_id"] = bc.user.id
        except Exception as e:
            print(f"get_business_conn refresh: {e}")
        return conn

    try:
        bc = await bot.get_business_connection(conn_id)
        conn = {
            "owner_id": bc.user.id,
            "muted": set(),
            "can_delete": bool(getattr(bc, "can_delete_all_messages", False)),
        }
        BUSINESS_CONNECTIONS[conn_id] = conn
        return conn
    except Exception as e:
        print(f"get_business_conn: {e}")
        return None


async def try_delete_business(conn_id: str, message_id: int) -> bool:
    try:
        await bot.delete_business_messages(
            business_connection_id=conn_id,
            message_ids=[message_id]
        )
        return True
    except Exception as e:
        print(f"delete_business_messages FAILED: {e}")
        return False


@dp.business_message()
async def on_business_message(message: types.Message):
    try:
        conn_id = message.business_connection_id
        user_id = message.from_user.id if message.from_user else None
        text = (message.text or "").strip()
        text_low = text.lower()

        if not conn_id:
            return

        conn = await get_business_conn(conn_id)
        if not conn:
            return

        owner_id = conn["owner_id"]
        is_from_owner = (user_id == owner_id)

        if text_low in (".help", ".хелп"):
            await try_delete_business(conn_id, message.message_id)
            try:
                await bot.send_message(
                    chat_id=message.chat.id,
                    text=BUSINESS_HELP_TEXT,
                )
            except Exception as e:
                print(f"send .хелп FAILED: {e}")
            return

        if is_from_owner and text_low == ".мут":
            target_id = message.chat.id
            target_name = message.chat.full_name or "собеседник"

            if target_id == owner_id:
                try:
                    await bot.send_message(
                        chat_id=message.chat.id,
                        text="❌ Нельзя замутить самого себя."
                    )
                except Exception:
                    pass
                return

            if not conn.get("can_delete", False):
                try:
                    await bot.send_message(
                        chat_id=message.chat.id,
                        text=(
                            "❌ <b>Не могу замутить собеседника.</b>\n\n"
                            "У бота нет права <b>«Удалять сообщения»</b>.\n"
                            "Без него я не смогу удалять сообщения собеседника.\n\n"
                            "<b>Как включить:</b>\n"
                            "1. Настройки Telegram → Telegram Business\n"
                            "2. → Чат-боты → твой бот\n"
                            "3. Включи право «Удалять сообщения»\n"
                            "4. Перезапусти бота\n\n"
                            "После этого напиши <code>.мут</code> снова."
                        )
                    )
                except Exception as e:
                    print(f"send warning FAILED: {e}")
                await try_delete_business(conn_id, message.message_id)
                return

            conn["muted"].add(target_id)

            await try_delete_business(conn_id, message.message_id)

            kb = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text="🔊 Размутить",
                    callback_data=f"biz_unmute:{conn_id}:{target_id}"
                )
            ]])

            try:
                await bot.send_message(
                    chat_id=message.chat.id,
                    text=(
                        f"🔇 Мут включён для <b>{target_name}</b>.\n"
                        f"Теперь его сообщения будут удаляться."
                    ),
                    reply_markup=kb
                )
            except Exception as e:
                print(f"send confirm FAILED: {e}")
            return

        if not is_from_owner and user_id in conn["muted"]:
            ok = await try_delete_business(conn_id, message.message_id)
            print(f"Удаление: {'OK' if ok else 'FAILED'}")
            return

    except Exception as e:
        print(f"!!! on_business_message ERROR: {e}")
        import traceback
        traceback.print_exc()


@dp.callback_query(lambda c: c.data.startswith("biz_unmute:"))
async def biz_unmute_callback(call: CallbackQuery):
    try:
        parts = call.data.split(":")
        if len(parts) != 3:
            await call.answer("Ошибка.", show_alert=True)
            return
        _, conn_id, user_id_str = parts
        try:
            user_id = int(user_id_str)
        except ValueError:
            await call.answer("Ошибка.", show_alert=True)
            return

        conn = await get_business_conn(conn_id)
        if not conn:
            await call.answer("Соединение неактивно.", show_alert=True)
            return

        if call.from_user.id != conn["owner_id"]:
            await call.answer("Размутить может только владелец.", show_alert=True)
            return

        conn["muted"].discard(user_id)
        try:
            await call.message.edit_text(
                "🔊 Пользователь размучен. Сообщения больше не удаляются."
            )
        except Exception:
            pass
        await call.answer("Готово")
    except Exception as e:
        print(f"biz_unmute error: {e}")
        await call.answer("Ошибка.", show_alert=True)


# ==================== УПРАВЛЕНИЕ СУПЕР-АДМИНАМИ ====================

@dp.message(Command("addsuper"))
async def cmd_addsuper(message: types.Message):
    if not is_super_admin(message):
        await message.reply("❌ Только супер-админы могут менять whitelist.")
        return
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.reply("❌ Формат: <code>/addsuper @username</code>")
        return
    uname = parts[1].lstrip("@").lower()
    SUPER_ADMINS.add(uname)
    await message.reply(f"✅ <code>@{uname}</code> добавлен в супер-админы.")


@dp.message(Command("delsuper"))
async def cmd_delsuper(message: types.Message):
    if not is_super_admin(message):
        await message.reply("❌ Только супер-админы могут менять whitelist.")
        return
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.reply("❌ Формат: <code>/delsuper @username</code>")
        return
    uname = parts[1].lstrip("@").lower()
    SUPER_ADMINS.discard(uname)
    await message.reply(f"✅ <code>@{uname}</code> удалён из супер-админов.")


@dp.message(Command("superlist"))
async def cmd_superlist(message: types.Message):
    if not is_super_admin(message):
        await message.reply("❌ Только для супер-админов.")
        return
    if not SUPER_ADMINS:
        await message.answer("📋 Список пуст.")
        return
    text = "📋 <b>Супер-админы:</b>\n" + "\n".join(
        f"• @{u}" for u in sorted(SUPER_ADMINS)
    )
    await message.answer(text)


# ==================== ПРОМОУТ / ДЕМОУТ ====================

@dp.message(Command("promote"))
@dp.message(Command("admin"))
async def cmd_promote(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        return
    if not await is_admin(message):
        await message.reply("❌ Только админы.")
        return
    if not await bot_can_promote(message):
        await message.reply("❌ У бота нет права назначать админов.")
        return

    user_id, name, err = await resolve_target(message)
    if err:
        await message.reply(err)
        return

    if user_id == BOT_ID:
        await message.reply("🤖 Нельзя назначить бота.")
        return
    if user_id == message.from_user.id:
        await message.reply("❌ Нельзя назначить самого себя.")
        return

    # защита супер-админов не нужна при промоуте

    try:
        await bot.promote_chat_member(
            chat_id=message.chat.id,
            user_id=user_id,
            can_manage_chat=True,
            can_delete_messages=True,
            can_manage_video_chats=True,
            can_restrict_members=True,
            can_promote_members=False,
            can_change_info=False,
            can_invite_users=True,
            can_pin_messages=True,
        )
        await message.answer(f"✅ <b>{name}</b> назначен администратором.")
    except Exception as e:
        await message.reply(f"❌ {e}")


@dp.message(Command("demote"))
@dp.message(Command("unadmin"))
async def cmd_demote(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        return
    if not await is_admin(message):
        await message.reply("❌ Только админы.")
        return
    if not await bot_can_promote(message):
        await message.reply("❌ У бота нет права снимать админов.")
        return

    user_id, name, err = await resolve_target(message)
    if err:
        await message.reply(err)
        return

    if user_id == BOT_ID:
        await message.reply("🤖 Нельзя снять бота.")
        return
    if user_id == message.from_user.id:
        await message.reply("❌ Нельзя снять самого себя.")
        return

    # нельзя снимать супер-админов
    for uname, cached_id in USERNAME_CACHE.get(message.chat.id, {}).items():
        if cached_id == user_id and uname in SUPER_ADMINS:
            await message.reply(f"🛡 <b>{name}</b> — супер-админ. Нельзя снять.")
            return
    if user_id in SUPER_ADMIN_IDS:
        await message.reply(f"🛡 <b>{name}</b> — супер-админ. Нельзя снять.")
        return

    try:
        await bot.promote_chat_member(
            chat_id=message.chat.id,
            user_id=user_id,
            can_manage_chat=False,
            can_delete_messages=False,
            can_manage_video_chats=False,
            can_restrict_members=False,
            can_promote_members=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False,
        )
        await message.answer(f"✅ <b>{name}</b> снят с администраторов.")
    except Exception as e:
        await message.reply(f"❌ {e}")


# ==================== КОМАНДЫ ====================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    cache_user(message.chat.id, message.from_user)
    await message.answer(
        "👋 Привет! Я бот-цензор.\n\n"
        "🛡 Удаляю мат автоматически\n"
        "🧹 Чищу сервисные сообщения\n"
        "📢 Созываю всех через /everyone\n"
        "🎲 Развлекательные команды\n"
        "🔨 Модерация + назначение админов\n"
        "🔠 Защита от капслока\n"
        "🔗 Защита от ссылок (кроме youtube.com/shorts)\n\n"
        "💼 Если я подключён к твоему Business-аккаунту, "
        "напиши мне в личку <code>.мут</code> или <code>.хелп</code>.\n\n"
        "📌 /help для списка команд."
    )


@dp.message(Command("help"))
@dp.message(Command("помощь"))
async def cmd_help(message: types.Message):
    await message.answer(
        "🛡 <b>Бот-цензор</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🎲 <b>Развлечения (для всех):</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "• /rps — КНБ с ботом\n"
        "• /rps @user или reply — КНБ с участником (с его согласия)\n"
        "• /duel @user или reply — вызвать на дуэль\n"
        "• /multi-duel 2 — коллективная дуэль на троих\n"
        "• /dice — бросить кубик (1–6)\n"
        "• /coin — орёл или решка\n"
        "• /ball &lt;вопрос&gt; — магический шар\n"
        "• /mafia — создать игру в мафию\n"
        "• /mafia_cancel — отменить набор (только создатель)\n"
        "• /mafia_extend — продлить набор на 30 секунд (только создатель)\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📊 <b>Статистика:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "• /актив или /stats — статистика пользователя\n"
        "• /whoareyou или «кто ты» — то же самое\n"
        "• Работает: reply, @username, без аргументов (про себя)\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📢 <b>Общее:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "• /everyone — созвать всех участников\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💼 <b>Business-режим (в личке):</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "• <code>.мут</code> — удалять сообщения собеседника\n"
        "• <code>.хелп</code> / <code>.help</code> — список команд\n"
        "• кнопка «🔊 Размутить» — снять мут\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🔨 <b>Администрация:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "<b>Удаление:</b>\n"
        "• /delete — удалить сообщение (reply)\n\n"
        "<b>Наказания:</b>\n"
        "• /kick — кикнуть (@user или reply)\n"
        "• /ban — забанить навсегда\n"
        "• /unban — разбанить (@user или ID)\n"
        "• /tempban &lt;мин&gt; — временный бан\n"
        "• /mute &lt;мин&gt; — мут (заглушить)\n"
        "• /vmute &lt;мин&gt; — мут голосовых\n"
        "• /unmute — снять все муты\n"
        "• /users — кого бот знает (для @username)\n\n"
        "<b>Назначение админов:</b>\n"
        "• /promote или /admin — назначить админом\n"
        "• /demote или /unadmin — снять с админки\n\n"
        "<b>Супер-админы:</b>\n"
        "• /addsuper @user — добавить в whitelist\n"
        "• /delsuper @user — убрать из whitelist\n"
        "• /superlist — список супер-админов\n\n"
        "<b>Управление ботом:</b>\n"
        "• /censor — включить цензуру\n"
        "• /uncensor — выключить цензуру\n"
        "• /censor_status — статус цензуры\n"
        "• /caps — включить защиту от капслока\n"
        "• /uncaps — выключить защиту от капслока\n"
        "• /caps_status — статус защиты от капслока\n"
        "• /links — включить защиту от ссылок\n"
        "• /unlinks — выключить защиту от ссылок\n"
        "• /links_status — статус защиты от ссылок\n"
        "• /service_on — вкл. чистку сервисных\n"
        "• /service_off — выкл. чистку\n"
        "• /service_status — статус чистки\n\n"
        "💡 <i>Команды администрации доступны админам чата. "
        "Отдельные пользователи из whitelist могут использовать их без прав.</i>\n\n"
        "🔗 <i>Защита от ссылок не блокирует https://www.youtube.com/shorts</i>"
    )


@dp.message(Command("censor"))
async def cmd_censor_on(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        return
    if not await is_admin(message):
        await message.reply("❌ Только админы.")
        return
    CENSOR_ENABLED[message.chat.id] = True
    await message.answer("✅ Цензура включена.")


@dp.message(Command("uncensor"))
async def cmd_censor_off(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        return
    if not await is_admin(message):
        await message.reply("❌ Только админы.")
        return
    CENSOR_ENABLED[message.chat.id] = False
    await message.answer("🔓 Цензура выключена.")


@dp.message(Command("censor_status"))
async def cmd_censor_status(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        return
    status = CENSOR_ENABLED.get(message.chat.id, True)
    await message.answer(f"Цензура: {'✅ вкл' if status else '🔓 выкл'}")


@dp.message(Command("caps"))
async def cmd_caps_on(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        return
    if not await is_admin(message):
        await message.reply("❌ Только админы.")
        return
    CAPS_ENABLED[message.chat.id] = True
    await message.answer("✅ Защита от капслока включена.")


@dp.message(Command("uncaps"))
async def cmd_caps_off(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        return
    if not await is_admin(message):
        await message.reply("❌ Только админы.")
        return
    CAPS_ENABLED[message.chat.id] = False
    await message.answer("🔓 Защита от капслока выключена.")


@dp.message(Command("caps_status"))
async def cmd_caps_status(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        return
    status = CAPS_ENABLED.get(message.chat.id, False)
    await message.answer(f"Защита от капслока: {'✅ вкл' if status else '🔓 выкл'}")


@dp.message(Command("links"))
async def cmd_links_on(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        return
    if not await is_admin(message):
        await message.reply("❌ Только админы.")
        return
    LINKS_ENABLED[message.chat.id] = True
    await message.answer("✅ Защита от ссылок включена (кроме youtube.com/shorts).")


@dp.message(Command("unlinks"))
async def cmd_links_off(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        return
    if not await is_admin(message):
        await message.reply("❌ Только админы.")
        return
    LINKS_ENABLED[message.chat.id] = False
    await message.answer("🔓 Защита от ссылок выключена.")


@dp.message(Command("links_status"))
async def cmd_links_status(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        return
    status = LINKS_ENABLED.get(message.chat.id, False)
    await message.answer(f"Защита от ссылок: {'✅ вкл' if status else '🔓 выкл'}")


@dp.message(Command("service_on"))
async def cmd_service_on(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        return
    if not await is_admin(message):
        return
    SERVICE_CLEANER_ENABLED[message.chat.id] = True
    await message.answer("✅ Чистка сервисных включена.")


@dp.message(Command("service_off"))
async def cmd_service_off(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        return
    if not await is_admin(message):
        return
    SERVICE_CLEANER_ENABLED[message.chat.id] = False
    await message.answer("🔓 Чистка сервисных выключена.")


@dp.message(Command("service_status"))
async def cmd_service_status(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        return
    status = SERVICE_CLEANER_ENABLED.get(message.chat.id, True)
    await message.answer(f"Чистка сервисных: {'✅ вкл' if status else '🔓 выкл'}")


@dp.message(Command("users"))
async def cmd_users(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        return
    if not await is_admin(message):
        await message.reply("❌ Только админы.")
        return

    await warm_cache(message.chat.id)
    cache = USERNAME_CACHE.get(message.chat.id, {})
    if not cache:
        await message.answer("👥 Кэш пуст. Пока никто не писал в чате.")
        return

    lines = []
    for uname, uid in sorted(cache.items()):
        name = get_name(message.chat.id, uid)
        lines.append(f"• @{uname} — {name}")
    text = "👥 <b>Кэш пользователей:</b>\n\n" + "\n".join(lines[:60])
    if len(lines) > 60:
        text += f"\n\n…и ещё {len(lines) - 60}"
    await message.answer(text)


@dp.message(Command("everyone"))
@dp.message(Command("все"))
async def cmd_everyone(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        return
    if not await is_admin(message):
        await message.reply("❌ Только админы могут созывать всех.")
        return

    await warm_cache(message.chat.id)
    chat_id = message.chat.id
    user_ids = set()

    cached = USERNAME_CACHE.get(chat_id, {})
    for uid in cached.values():
        user_ids.add(uid)

    try:
        admins = await bot.get_chat_administrators(chat_id)
        for admin in admins:
            if not admin.user.is_bot:
                user_ids.add(admin.user.id)
    except Exception as e:
        print(f"get_chat_administrators: {e}")

    user_ids.add(message.from_user.id)

    real_ids = []
    for uid in user_ids:
        try:
            member = await bot.get_chat_member(chat_id, uid)
            if member.user.is_bot:
                continue
            if member.status in ("left", "kicked"):
                continue
            real_ids.append(uid)
        except Exception:
            continue

    if not real_ids:
        await message.answer("⚠️ Не удалось собрать участников.")
        return

    mentions = " ".join(
        f'<a href="tg://user?id={uid}">\u200b</a>' for uid in real_ids[:40]
    )

    text = (
        "📢 <b>Внимание всем!</b>\n"
        f"{mentions}\n"
        f"🔔 {message.from_user.mention_html()} созывает всех!"
    )

    try:
        await message.answer(text)
    except Exception as e:
        await message.reply(f"❌ {e}")


@dp.message(Command("delete"))
async def cmd_delete(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        return
    if not await is_admin(message):
        try:
            await message.delete()
        except Exception:
            pass
        return
    if not message.reply_to_message:
        try:
            await message.delete()
        except Exception:
            pass
        return
    try:
        await bot.delete_message(message.chat.id, message.reply_to_message.message_id)
    except Exception as e:
        print(f"delete target: {e}")
    try:
        await message.delete()
    except Exception as e:
        print(f"delete cmd: {e}")


# ==================== КНБ ====================

RPS_CHOICES = {"rock": "✊ Камень", "scissors": "✌️ Ножницы", "paper": "✋ Бумага"}
RPS_BEATS = {"rock": "scissors", "scissors": "paper", "paper": "rock"}


def rps_result(a, b):
    if a == b:
        return "draw"
    if RPS_BEATS[a] == b:
        return "a"
    return "b"


def rps_keyboard(game_id):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✊", callback_data=f"rps:{game_id}:rock"),
        InlineKeyboardButton(text="✌️", callback_data=f"rps:{game_id}:scissors"),
        InlineKeyboardButton(text="✋", callback_data=f"rps:{game_id}:paper"),
    ], [InlineKeyboardButton(text="❌ Отменить", callback_data=f"rpsc:{game_id}")]])


def rps_invite_keyboard(invite_id):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Принять", callback_data=f"rpsi:{invite_id}:yes"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"rpsi:{invite_id}:no"),
    ]])


def rps_rematch_keyboard(rematch_id, count=0):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=f"🔄 Реванш ({count}/2)",
            callback_data=f"rpsr:{rematch_id}"
        )
    ], [InlineKeyboardButton(text="❌ Отменить", callback_data=f"rpsrc:{rematch_id}")]])


def make_game_id(chat_id, user_id):
    return f"{chat_id}_{user_id}_{random.randint(100000, 999999)}"




def update_pair_stats(store, game, winner_id=None):
    key = (game["chat_id"], min(game["player_a"], game["player_b"]), max(game["player_a"], game["player_b"]))
    stats = store.setdefault(key, {"games": 0, "wins_a": 0, "wins_b": 0, "draws": 0})
    stats["games"] += 1
    if winner_id is None:
        stats["draws"] += 1
    elif winner_id == game["player_a"]:
        stats["wins_a"] += 1
    else:
        stats["wins_b"] += 1
    return stats

def pair_score_text(store, game):
    key = (game["chat_id"], min(game["player_a"], game["player_b"]), max(game["player_a"], game["player_b"]))
    st = store.get(key, {"games": 0, "wins_a": 0, "wins_b": 0, "draws": 0})
    if game["player_a"] <= game["player_b"]:
        score = f"{st['wins_a']}:{st['wins_b']}"
    else:
        score = f"{st['wins_b']}:{st['wins_a']}"
    return f"📊 Матчей: {st['games']} | Счёт: <b>{score}</b> | Ничьих: {st['draws']}"

# ==================== ДУЭЛИ ====================

DUEL_GAMES = {}
DUEL_INVITES = {}
DUEL_REMATCH = {}
DUEL_STATS = {}
RPS_STATS = {}
MULTI_DUELS = {}


def duel_keyboard(game_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎯 Прицелиться", callback_data=f"duel:{game_id}:aim"),
            InlineKeyboardButton(text="🔫 Выстрелить", callback_data=f"duel:{game_id}:shoot"),
        ],
        [
            InlineKeyboardButton(text="💨 Сбросить прицел соперника", callback_data=f"duel:{game_id}:reset"),
        ],
        [
            InlineKeyboardButton(text="🛡 Уклониться", callback_data=f"duel:{game_id}:dodge"),
        ],
        [InlineKeyboardButton(text="❌ Отменить", callback_data=f"duelc:{game_id}")],
    ])


def duel_invite_keyboard(invite_id):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Принять", callback_data=f"dueli:{invite_id}:yes"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"dueli:{invite_id}:no"),
    ]])


def duel_rematch_keyboard(rematch_id, count=0):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=f"🔄 Реванш ({count}/2)",
            callback_data=f"duelr:{rematch_id}"
        )
    ], [InlineKeyboardButton(text="❌ Отменить", callback_data=f"duelrc:{rematch_id}")]])


def create_duel(data):
    game_id = make_game_id(data["chat_id"], data["a_id"])
    DUEL_GAMES[game_id] = {
        "chat_id": data["chat_id"],
        "player_a": data["a_id"],
        "player_b": data["b_id"],
        "a_name": data["a_name"],
        "b_name": data["b_name"],
        "a_mention": data["a_mention"],
        "b_mention": data["b_mention"],
        "turn": "a",
        "aim_a": 0,
        "aim_b": 0,
        "dodge_a": False,
        "dodge_b": False,
    }
    return game_id


def duel_chance(aim):
    # 20% без прицела, +15% за каждый уровень, максимум 90%.
    return min(90, 20 + aim * 15)


def duel_status(game):
    return (
        f"🎯 Прицел {game['a_mention']}: <b>{game['aim_a']}</b> "
        f"({duel_chance(game['aim_a'])}%)\n"
        f"🎯 Прицел {game['b_mention']}: <b>{game['aim_b']}</b> "
        f"({duel_chance(game['aim_b'])}%)\n\n"
        f"🛡 Уклонение {game['a_mention']}: "
        f"{'готово' if game['dodge_a'] else 'нет'}\n"
        f"🛡 Уклонение {game['b_mention']}: "
        f"{'готово' if game['dodge_b'] else 'нет'}"
    )


@dp.message(Command("duel"))
@dp.message(Command("дуэль"))
async def cmd_duel(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        await message.reply("❌ Дуэли доступны только в группах.")
        return

    if not message.from_user:
        return

    cache_user(message.chat.id, message.from_user)
    target_id, target_name = await resolve_target_for_rps(message)

    if target_id is None:
        await message.reply(
            "❌ Укажи соперника через reply или @username.\n"
            "Пример: <code>/duel @username</code>"
        )
        return

    if target_id == message.from_user.id:
        await message.reply("❌ Нельзя вызвать на дуэль самого себя.")
        return

    if target_id == BOT_ID:
        await message.reply("🤖 Бота нельзя вызвать на дуэль.")
        return

    # Не даём одному человеку получать несколько активных приглашений в этом чате.
    if any(
        inv["chat_id"] == message.chat.id and inv["to_id"] == target_id
        for inv in DUEL_INVITES.values()
    ):
        await message.reply("❌ У этого пользователя уже есть приглашение на дуэль.")
        return

    invite_id = f"{message.chat.id}_{random.randint(1000000, 9999999)}"
    DUEL_INVITES[invite_id] = {
        "chat_id": message.chat.id,
        "a_id": message.from_user.id,
        "b_id": target_id,
        "a_name": message.from_user.full_name,
        "b_name": target_name,
        "a_mention": message.from_user.mention_html(),
        "b_mention": f'<a href="tg://user?id={target_id}">{target_name}</a>',
    }

    await message.answer(
        f"⚔️ <b>Вызов на дуэль!</b>\n\n"
        f"{message.from_user.mention_html()} вызывает "
        f'<a href="tg://user?id={target_id}">{target_name}</a>.\n'
        f"Первым ходит вызывающий.\n\n"
        f"Принять вызов?",
        reply_markup=duel_invite_keyboard(invite_id)
    )


async def handle_duel_callback(call: CallbackQuery) -> bool:
    data = call.data or ""

    if data.startswith("duelc:"):
        game_id = data.split(":", 1)[1]
        game = DUEL_GAMES.get(game_id)
        if not game or call.from_user.id not in (game["player_a"], game["player_b"]):
            await call.answer("Отменить может только участник.", show_alert=True); return True
        DUEL_GAMES.pop(game_id, None)
        await call.message.edit_text("❌ Дуэль отменена участником.")
        await call.answer("Дуэль отменена."); return True
    if data.startswith("duelrc:"):
        rid = data.split(":", 1)[1]; rem = DUEL_REMATCH.get(rid)
        if not rem or call.from_user.id not in rem["players"]:
            await call.answer("Недоступно.", show_alert=True); return True
        DUEL_REMATCH.pop(rid, None)
        await call.message.edit_text("❌ Реванш отменён."); await call.answer("Отменено."); return True

    # Принятие или отклонение приглашения.
    if data.startswith("dueli:"):
        parts = data.split(":")
        if len(parts) != 3:
            await call.answer("Ошибка приглашения.", show_alert=True)
            return True

        _, invite_id, action = parts
        invite = DUEL_INVITES.get(invite_id)
        if not invite:
            await call.answer("Приглашение уже недоступно.", show_alert=True)
            return True

        if call.from_user.id != invite["b_id"]:
            await call.answer("Это приглашение не тебе.", show_alert=True)
            return True

        DUEL_INVITES.pop(invite_id, None)

        if action == "no":
            await call.message.edit_text(
                f"⚔️ <b>Дуэль отклонена.</b>\n\n{invite['b_mention']} "
                f"отклонил вызов от {invite['a_mention']}."
            )
            await call.answer("Вызов отклонён.")
            return True

        game_id = create_duel(invite)
        game = DUEL_GAMES[game_id]
        await call.message.edit_text(
            f"⚔️ <b>ДУЭЛЬ НАЧАЛАСЬ!</b>\n\n"
            f"{game['a_mention']} против {game['b_mention']}\n\n"
            f"Первым ходит вызывающий: {game['a_mention']}\n\n"
            f"{duel_status(game)}",
            reply_markup=duel_keyboard(game_id)
        )
        await call.answer("Дуэль принята!")
        return True

    # Реванш: должны согласиться оба участника.
    if data.startswith("duelr:"):
        rematch_id = data.split(":", 1)[1]
        rematch = DUEL_REMATCH.get(rematch_id)
        if not rematch:
            await call.answer("Реванш уже недоступен.", show_alert=True)
            return True

        user_id = call.from_user.id
        if user_id not in rematch["players"]:
            await call.answer("Реванш доступен только участникам.", show_alert=True)
            return True

        if user_id in rematch["clicked"]:
            await call.answer("Ты уже согласился на реванш.", show_alert=True)
            return True

        rematch["clicked"].add(user_id)
        count = len(rematch["clicked"])

        if count < 2:
            try:
                await call.message.edit_reply_markup(
                    reply_markup=duel_rematch_keyboard(rematch_id, count)
                )
            except Exception:
                pass
            await call.answer(f"Согласны на реванш: {count}/2")
            return True

        DUEL_REMATCH.pop(rematch_id, None)
        game_id = create_duel(rematch)
        game = DUEL_GAMES[game_id]
        await call.message.edit_text(
            f"⚔️ <b>РЕВАНШ!</b>\n\n"
            f"{game['a_mention']} против {game['b_mention']}\n\n"
            f"Первым снова ходит вызывающий: {game['a_mention']}\n\n"
            f"{duel_status(game)}",
            reply_markup=duel_keyboard(game_id)
        )
        await call.answer("Реванш начинается!")
        return True

    # Ход в дуэли.
    if data.startswith("duel:"):
        parts = data.split(":")
        if len(parts) != 3:
            await call.answer("Ошибка хода.", show_alert=True)
            return True

        _, game_id, action = parts
        game = DUEL_GAMES.get(game_id)
        if not game:
            await call.answer("Дуэль уже завершена.", show_alert=True)
            return True

        user_id = call.from_user.id
        if user_id == game["player_a"]:
            slot, enemy = "a", "b"
        elif user_id == game["player_b"]:
            slot, enemy = "b", "a"
        else:
            await call.answer("Ты не участник этой дуэли.", show_alert=True)
            return True

        if game["turn"] != slot:
            await call.answer("Сейчас ход соперника.", show_alert=True)
            return True

        if action not in ("aim", "shoot", "reset", "dodge"):
            await call.answer("Неизвестное действие.", show_alert=True)
            return True

        # Выстрел разрешается сразу, проверяя уклонение противника.
        if action == "aim":
            game[f"aim_{slot}"] += 1
            result_line = (
                f"🎯 {game[f'{slot}_mention']} прицеливается. "
                f"Точность теперь <b>{duel_chance(game[f'aim_{slot}'])}%</b>."
            )
        elif action == "reset":
            game[f"aim_{enemy}"] = 0
            result_line = (
                f"💨 {game[f'{slot}_mention']} сбрасывает прицел соперника!"
            )
        elif action == "dodge":
            game[f"dodge_{slot}"] = True
            result_line = (
                f"🛡 {game[f'{slot}_mention']} приготовился уклониться "
                f"от следующего выстрела."
            )
        else:  # shoot
            chance = duel_chance(game[f"aim_{slot}"])
            if game[f"dodge_{enemy}"]:
                game[f"dodge_{enemy}"] = False
                game[f"aim_{slot}"] = 0
                result_line = (
                    f"🔫 {game[f'{slot}_mention']} стреляет, но "
                    f"{game[f'{enemy}_mention']} уклоняется!\n"
                    f"🎯 Прицел стрелявшего сброшен."
                )
            elif random.randint(1, 100) <= chance:
                winner_mention = game[f"{slot}_mention"]
                loser_mention = game[f"{enemy}_mention"]
                rematch_id = (
                    f"{game['chat_id']}_{game['player_a']}_"
                    f"{game['player_b']}_{random.randint(10000, 99999)}"
                )
                DUEL_REMATCH[rematch_id] = {
                    "players": {game["player_a"], game["player_b"]},
                    "clicked": set(),
                    "chat_id": game["chat_id"],
                    "a_id": game["player_a"],
                    "b_id": game["player_b"],
                    "a_name": game["a_name"],
                    "b_name": game["b_name"],
                    "a_mention": game["a_mention"],
                    "b_mention": game["b_mention"],
                }
                stats = update_pair_stats(DUEL_STATS, game, game[f"player_{slot}"])
                score_line = pair_score_text(DUEL_STATS, game)
                DUEL_GAMES.pop(game_id, None)
                await call.message.edit_text(
                    f"⚔️ <b>ДУЭЛЬ ЗАВЕРШЕНА!</b>\n\n"
                    f"🔫 {winner_mention} попадает в {loser_mention}!\n"
                    f"🎯 Точность выстрела: <b>{chance}%</b>\n\n"
                    f"🏆 Победитель: {winner_mention}\n"
                    f"{score_line}\n\n"
                    f"Хотите реванш?",
                    reply_markup=duel_rematch_keyboard(rematch_id)
                )
                await call.answer("Попадание!")
                return True
            else:
                game[f"aim_{slot}"] = 0
                result_line = (
                    f"🔫 {game[f'{slot}_mention']} промахивается!\n"
                    f"🎯 Его прицел сброшен."
                )

        # После любого действия ход переходит сопернику.
        game["turn"] = enemy
        next_mention = game[f"{enemy}_mention"]
        await call.message.edit_text(
            f"⚔️ <b>ДУЭЛЬ</b>\n\n"
            f"{game['a_mention']} против {game['b_mention']}\n\n"
            f"{result_line}\n\n"
            f"{duel_status(game)}\n\n"
            f"👉 Следующий ход: {next_mention}",
            reply_markup=duel_keyboard(game_id)
        )
        await call.answer("Ход выполнен.")
        return True

    return False



@dp.message(Command("rps"))
@dp.message(Command("кнб"))
async def cmd_rps(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        await message.reply("❌ Только в группах.")
        return

    cache_user(message.chat.id, message.from_user)
    target_id, target_name = await resolve_target_for_rps(message)

    if target_id is None:
        game_id = make_game_id(message.chat.id, message.from_user.id)
        bot_choice_key = random.choice(list(RPS_CHOICES.keys()))
        RPS_GAMES[game_id] = {
            "player_a": message.from_user.id,
            "player_b": BOT_ID,
            "choice_a": None,
            "choice_b": bot_choice_key,
            "turn": "a",
            "is_bot": True,
            "a_name": message.from_user.full_name,
            "a_mention": message.from_user.mention_html(),
            "b_name": "🤖 Бот",
            "b_mention": "🤖 Бот",
            "chat_id": message.chat.id,
        }
        await message.answer(
            f"🎮 <b>КНБ с ботом</b>\n\n"
            f"👤 {message.from_user.mention_html()}, твой ход:",
            reply_markup=rps_keyboard(game_id)
        )
        return

    if target_id == message.from_user.id:
        await message.reply("❌ Нельзя играть с самим собой.")
        return

    if target_id == BOT_ID:
        await message.reply("🤖 Чтобы сыграть со мной, напиши /rps без аргументов.")
        return

    invite_id = f"{message.chat.id}_{random.randint(1000000, 9999999)}"
    RPS_INVITES[invite_id] = {
        "chat_id": message.chat.id,
        "from_id": message.from_user.id,
        "from_name": message.from_user.full_name,
        "from_mention": message.from_user.mention_html(),
        "to_id": target_id,
        "to_name": target_name,
    }

    try:
        await message.answer(
            f"🎮 <b>Вызов на КНБ!</b>\n\n"
            f"👤 {message.from_user.mention_html()} приглашает "
            f"<a href=\"tg://user?id={target_id}\">{target_name}</a>\n\n"
            f"Ожидаю ответа...",
            reply_markup=rps_invite_keyboard(invite_id)
        )
    except Exception as e:
        await message.reply(f"❌ {e}")


async def resolve_target_for_rps(message: types.Message):
    chat_id = message.chat.id

    if message.reply_to_message and message.reply_to_message.from_user:
        u = message.reply_to_message.from_user
        cache_user(chat_id, u)
        return u.id, u.full_name

    text = message.text or ""

    if message.entities:
        for entity in message.entities:
            if entity.type == "text_mention" and entity.user:
                u = entity.user
                cache_user(chat_id, u)
                return u.id, u.full_name
            if entity.type == "mention":
                username = text[entity.offset:entity.offset + entity.length]
                uid = resolve_username(chat_id, username)
                if uid:
                    return uid, get_name(chat_id, uid)
                return None, None

    username = extract_username_from_text(text)
    if username:
        uid = resolve_username(chat_id, username)
        if uid:
            return uid, get_name(chat_id, uid)

    return None, None


@dp.callback_query(lambda c: (c.data or "").startswith(("rps:", "rpsi:", "rpsr:", "rpsc:", "rpsrc:", "duel:", "dueli:", "duelr:", "duelc:", "duelrc:")))
async def rps_callback(call: CallbackQuery):
    if await handle_duel_callback(call):
        return

    if call.data.startswith("rpsc:"):
        gid = call.data.split(":", 1)[1]; game = RPS_GAMES.get(gid)
        if not game or call.from_user.id not in (game["player_a"], game["player_b"]):
            await call.answer("Отменить может только участник.", show_alert=True); return
        RPS_GAMES.pop(gid, None); await call.message.edit_text("❌ Игра в КНБ отменена."); await call.answer("Отменено."); return
    if call.data.startswith("rpsrc:"):
        rid = call.data.split(":", 1)[1]; rem = RPS_REMATCH.get(rid)
        if not rem or call.from_user.id not in rem["players"]:
            await call.answer("Недоступно.", show_alert=True); return
        RPS_REMATCH.pop(rid, None); await call.message.edit_text("❌ Реванш отменён."); await call.answer("Отменено."); return

    # --- реванш ---
    if call.data.startswith("rpsr:"):
        rematch_id = call.data.split(":", 1)[1]
        data = RPS_REMATCH.get(rematch_id)
        if not data:
            await call.answer("Реванш уже недоступен.", show_alert=True)
            try:
                await call.message.edit_reply_markup(reply_markup=None)
            except Exception:
                pass
            return

        uid = call.from_user.id
        if uid not in data["players"]:
            await call.answer("Реванш только для участников этой игры.", show_alert=True)
            return

        if uid in data["clicked"]:
            await call.answer("Ты уже нажал реванш.", show_alert=True)
            return

        data["clicked"].add(uid)
        count = len(data["clicked"])

        if count < 2:
            try:
                await call.message.edit_reply_markup(
                    reply_markup=rps_rematch_keyboard(rematch_id, count)
                )
            except Exception:
                pass
            await call.answer(f"Реванш: {count}/2")
            return

        # оба нажали — стартуем новую игру
        await call.answer("Реванш!")
        RPS_REMATCH.pop(rematch_id, None)

        game_id = make_game_id(data["chat_id"], data["a_id"])
        RPS_GAMES[game_id] = {
            "player_a": data["a_id"],
            "player_b": data["b_id"],
            "choice_a": None,
            "choice_b": None,
            "turn": "a",
            "is_bot": False,
            "a_name": data["a_name"],
            "a_mention": data["a_mention"],
            "b_name": data["b_name"],
            "b_mention": data["b_mention"],
            "chat_id": data["chat_id"],
        }

        try:
            await call.message.edit_text(
                f"🎮 <b>Реванш!</b>\n\n"
                f"🥊 {data['a_mention']} vs {data['b_mention']}\n\n"
                f"👉 <b>{data['a_name']}</b>, выбери ход первым:",
                reply_markup=rps_keyboard(game_id)
            )
        except Exception:
            pass
        return

    # --- приглашение ---
    if call.data.startswith("rpsi:"):
        parts = call.data.split(":")
        if len(parts) != 3:
            await call.answer("Ошибка.", show_alert=True)
            return
        _, invite_id, action = parts
        invite = RPS_INVITES.get(invite_id)
        if not invite:
            await call.answer("Приглашение не найдено.", show_alert=True)
            return

        if call.from_user.id != invite["to_id"]:
            await call.answer("Это приглашение не тебе.", show_alert=True)
            return

        if action == "no":
            try:
                await call.message.edit_text(
                    f"🎮 <b>КНБ</b>\n\n"
                    f"❌ <a href=\"tg://user?id={invite['to_id']}\">{invite['to_name']}</a> "
                    f"отклонил приглашение от {invite['from_mention']}.",
                    reply_markup=None
                )
            except Exception:
                pass
            await call.answer("Отклонено.")
            RPS_INVITES.pop(invite_id, None)
            return

        await call.answer("Принято!")
        game_id = make_game_id(invite["chat_id"], invite["from_id"])
        RPS_GAMES[game_id] = {
            "player_a": invite["from_id"],
            "player_b": invite["to_id"],
            "choice_a": None,
            "choice_b": None,
            "turn": "a",
            "is_bot": False,
            "a_name": invite["from_name"],
            "a_mention": invite["from_mention"],
            "b_name": invite["to_name"],
            "b_mention": f'<a href="tg://user?id={invite["to_id"]}">{invite["to_name"]}</a>',
            "chat_id": invite["chat_id"],
        }
        try:
            await call.message.edit_text(
                f"🎮 <b>КНБ!</b>\n\n"
                f"🥊 {invite['from_mention']} vs "
                f"<a href=\"tg://user?id={invite['to_id']}\">{invite['to_name']}</a>\n\n"
                f"👉 <b>{invite['from_name']}</b>, выбери свой ход первым:",
                reply_markup=rps_keyboard(game_id)
            )
        except Exception:
            pass
        RPS_INVITES.pop(invite_id, None)
        return

    # --- ход ---
    if call.data.startswith("rps:"):
        parts = call.data.split(":")
        if len(parts) != 3:
            await call.answer("Ошибка.", show_alert=True)
            return

        _, game_id, choice = parts
        game = RPS_GAMES.get(game_id)
        if not game:
            await call.answer("Игра завершена.", show_alert=True)
            try:
                await call.message.edit_reply_markup(reply_markup=None)
            except Exception:
                pass
            return

        user_id = call.from_user.id

        if game["is_bot"]:
            if user_id != game["player_a"]:
                await call.answer("Не твоя игра.", show_alert=True)
                return
            bot_choice = game["choice_b"]
            result = rps_result(choice, bot_choice)
            if result == "draw":
                verdict = "🤝 Ничья!"
            elif result == "a":
                verdict = f"🎉 Победил {game['a_name']}!"
            else:
                verdict = "😢 Победил бот!"

            # для игры с ботом реванш не делаем (или можно, но пока только PvP)
            try:
                await call.message.edit_text(
                    f"🎮 <b>КНБ</b>\n\n"
                    f"👤 {RPS_CHOICES[choice]}\n🤖 {RPS_CHOICES[bot_choice]}\n\n"
                    f"<b>{verdict}</b>",
                    reply_markup=None
                )
            except Exception:
                pass
            await call.answer()
            RPS_GAMES.pop(game_id, None)
            return

        slot = "a" if user_id == game["player_a"] else ("b" if user_id == game["player_b"] else None)
        if slot is None:
            await call.answer("Не участник.", show_alert=True)
            return

        if game["turn"] != slot:
            await call.answer("Сейчас не твой ход!", show_alert=True)
            return

        if game.get(f"choice_{slot}") is not None:
            await call.answer("Уже выбрал!", show_alert=True)
            return

        game[f"choice_{slot}"] = choice
        await call.answer(f"Выбрал: {RPS_CHOICES[choice]}")

        if game["choice_a"] is not None and game["choice_b"] is not None:
            ca, cb = game["choice_a"], game["choice_b"]
            result = rps_result(ca, cb)
            if result == "draw":
                verdict = "🤝 Ничья!"
            elif result == "a":
                verdict = f"🏆 Победил {game['a_mention']}!"
            else:
                verdict = f"🏆 Победил {game['b_mention']}!"

            winner_id = None if result == "draw" else (game["player_a"] if result == "a" else game["player_b"])
            update_pair_stats(RPS_STATS, game, winner_id)
            score_line = pair_score_text(RPS_STATS, game)
            # создаём реванш
            rematch_id = f"{game['chat_id']}_{game['player_a']}_{game['player_b']}_{random.randint(10000, 99999)}"
            RPS_REMATCH[rematch_id] = {
                "players": {game["player_a"], game["player_b"]},
                "clicked": set(),
                "chat_id": game["chat_id"],
                "a_id": game["player_a"],
                "b_id": game["player_b"],
                "a_name": game["a_name"],
                "b_name": game["b_name"],
                "a_mention": game["a_mention"],
                "b_mention": game["b_mention"],
            }

            try:
                await call.message.edit_text(
                    f"🎮 <b>КНБ результат</b>\n\n"
                    f"👤 {game['a_mention']}: {RPS_CHOICES[ca]}\n"
                    f"👤 {game['b_mention']}: {RPS_CHOICES[cb]}\n\n"
                    f"<b>{verdict}</b>\n\n{score_line}",
                    reply_markup=rps_rematch_keyboard(rematch_id, 0)
                )
            except Exception:
                pass
            RPS_GAMES.pop(game_id, None)
            return

        if slot == "a":
            game["turn"] = "b"
            next_mention = game["b_mention"]
        else:
            game["turn"] = "a"
            next_mention = game["a_mention"]

        try:
            await call.message.edit_text(
                f"🎮 <b>КНБ</b>\n\n"
                f"🥊 {game['a_mention']} vs {game['b_mention']}\n\n"
                f"👉 Теперь ход: {next_mention}",
                reply_markup=rps_keyboard(game_id)
            )
        except Exception:
            pass
        return

    await call.answer()


# ==================== РАЗВЛЕКАТЕЛЬНЫЕ ====================

@dp.message(Command("dice"))
@dp.message(Command("кубик"))
async def cmd_dice(message: types.Message):
    await message.answer(f"🎲 Выпало: <b>{random.randint(1, 6)}</b>")


@dp.message(Command("coin"))
@dp.message(Command("монетка"))
async def cmd_coin(message: types.Message):
    await message.answer(f"Подбрасываю... <b>{random.choice(['🪙 Орёл', '🪙 Решка'])}</b>")


@dp.message(Command("ball"))
@dp.message(Command("шар"))
async def cmd_ball(message: types.Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer("🔮 Задай вопрос: <code>/ball Вопрос?</code>")
        return
    await message.answer(f"❓ <i>{parts[1].strip()}</i>\n\n{random.choice(MAGIC_8_BALL)}")


# ==================== МОДЕРАЦИЯ ====================

@dp.message(Command("kick"))
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
        await message.reply(f"❌ {e}")


@dp.message(Command("ban"))
async def cmd_ban(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ Только админы.")
        return
    if not await bot_can_restrict(message):
        await message.reply("❌ Нет прав.")
        return
    user_id, name, err = await resolve_target(message)
    if err:
        await message.reply(err)
        return
    if not await check_target(message, user_id, name):
        return
    try:
        await bot.ban_chat_member(message.chat.id, user_id)
        await message.answer(f"🔨 {name} забанен.")
    except Exception as e:
        await message.reply(f"❌ {e}")


@dp.message(Command("unban"))
async def cmd_unban(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ Только админы.")
        return
    if not await bot_can_restrict(message):
        await message.reply("❌ Нет прав.")
        return
    user_id, name, err = await resolve_target(message)
    if err:
        await message.reply(err)
        return
    try:
        await bot.unban_chat_member(message.chat.id, user_id, only_if_banned=True)
        await message.answer(f"🔓 {name} разбанен.")
    except Exception as e:
        await message.reply(f"❌ {e}")


@dp.message(Command("tempban"))
async def cmd_tempban(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ Только админы.")
        return
    if not await bot_can_restrict(message):
        await message.reply("❌ Нет прав.")
        return
    user_id, name, err = await resolve_target(message)
    if err:
        await message.reply(err)
        return
    if not await check_target(message, user_id, name):
        return
    minutes = parse_minutes((message.text or "").split())
    if not minutes:
        await message.reply("❌ Укажи минуты: /tempban 30")
        return
    try:
        until_ts = int((datetime.now() + timedelta(minutes=minutes)).timestamp())
        await bot.ban_chat_member(message.chat.id, user_id, until_date=until_ts)
        await message.answer(f"⏱ {name} забанен на <b>{minutes} мин.</b>")
    except Exception as e:
        await message.reply(f"❌ {e}")


@dp.message(Command("mute"))
async def cmd_mute(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ Только админы.")
        return
    if not await bot_can_restrict(message):
        await message.reply("❌ Нет прав.")
        return
    user_id, name, err = await resolve_target(message)
    if err:
        await message.reply(err)
        return
    if not await check_target(message, user_id, name):
        return
    minutes = parse_minutes((message.text or "").split())
    if not minutes:
        await message.reply("❌ Укажи минуты: /mute @user 15")
        return
    try:
        until_ts = int((datetime.now() + timedelta(minutes=minutes)).timestamp())
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=user_id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_ts
        )
        await message.answer(f"🔇 {name} замучен на <b>{minutes} мин.</b>")
    except Exception as e:
        await message.reply(f"❌ {e}")


@dp.message(Command("vmute"))
async def cmd_vmute(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ Только админы.")
        return
    if not await bot_can_restrict(message):
        await message.reply("❌ Нет прав.")
        return
    user_id, name, err = await resolve_target(message)
    if err:
        await message.reply(err)
        return
    if not await check_target(message, user_id, name):
        return
    minutes = parse_minutes((message.text or "").split())
    if not minutes:
        await message.reply("❌ Укажи минуты: /vmute @user 15")
        return
    try:
        until_ts = int((datetime.now() + timedelta(minutes=minutes)).timestamp())
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_audios=False,
                can_send_documents=False,
                can_send_photos=False,
                can_send_videos=False,
                can_send_video_notes=False,
                can_send_voice_notes=False,
                can_send_polls=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False,
            ),
            until_date=until_ts
        )
        await message.answer(f"🎙 {name} — мут голосовых на <b>{minutes} мин.</b>")
    except Exception as e:
        await message.reply(f"❌ {e}")


@dp.message(Command("unmute"))
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
        await message.answer(f"🔊 {name} размучен (все права возвращены).")
    except Exception as e:
        await message.reply(f"❌ {e}")




# ==================== КОЛЛЕКТИВНАЯ ДУЭЛЬ ====================

def multi_duel_keyboard(game_id, game):
    rows = []
    if game["phase"] == "lobby":
        rows.append([InlineKeyboardButton(
            text=f"➕ Участвовать ({len(game['players'])}/{game['limit']+1})",
            callback_data=f"mdjoin:{game_id}"
        )])
    else:
        rows.extend([
            [InlineKeyboardButton(text="🎯 Прицелиться", callback_data=f"mdact:{game_id}:aim")],
            [InlineKeyboardButton(text="🔫 Выстрелить", callback_data=f"mdact:{game_id}:shoot")],
            [InlineKeyboardButton(text="🛡 Уклониться", callback_data=f"mdact:{game_id}:dodge")],
        ])
    rows.append([InlineKeyboardButton(text="❌ Отменить", callback_data=f"mdcancel:{game_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def multi_duel_text(game, note=""):
    alive = [game["players"][x] for x in game["alive"]]
    text = "⚔️ <b>Коллективная дуэль</b>\n"
    if note:
        text += f"\n{note}\n"
    text += "\nУчастники:\n" + "\n".join(
        f"{'🟢' if uid in game['alive'] else '💀'} {name}"
        for uid, name in game["players"].items()
    )
    if game["phase"] == "lobby":
        text += f"\n\nНабор: {len(game['players'])}/{game['limit']+1}"
        text += "\nПрисоединиться могут только приглашённые игроки."
    elif game["phase"] == "active":
        text += f"\n\n🎮 Ход: <b>{game['players'][game['current_uid']]}</b>"
        text += "\nВыбери действие: прицелиться, выстрелить или уклониться."
    return text


@dp.message(Command("multi-duel"))
async def cmd_multi_duel(message: types.Message):
    if message.chat.type == ChatType.PRIVATE or not message.from_user:
        return
    args = (message.text or "").split()
    try:
        extra = int(args[1])
    except (IndexError, ValueError):
        await message.reply("Использование: /multi-duel 2 — создатель и ещё 2 приглашённых игрока.")
        return
    if not 2 <= extra <= 9:
        await message.reply("Укажите от 2 до 9 приглашённых игроков.")
        return

    # Поддерживаем все варианты Telegram-упоминаний: выбранное имя (text_mention),
    # обычное @username, tg://user?id=..., ответ на сообщение и числовые ID.
    invited = set()
    text = message.text or ""

    if message.reply_to_message and message.reply_to_message.from_user:
        replied_user = message.reply_to_message.from_user
        if not replied_user.is_bot:
            invited.add(replied_user.id)
            cache_user(message.chat.id, replied_user)

    def entity_text(entity):
        # Telegram offsets измеряются в UTF-16 code units.
        raw = text.encode("utf-16-le")
        return raw[entity.offset * 2:(entity.offset + entity.length) * 2].decode("utf-16-le", errors="ignore")

    unresolved = []
    for ent in (message.entities or []):
        if ent.type == "text_mention" and ent.user:
            if not ent.user.is_bot:
                invited.add(ent.user.id)
                cache_user(message.chat.id, ent.user)
        elif ent.type == "mention":
            username = entity_text(ent).lstrip("@")
            uid = resolve_username(message.chat.id, username)
            if uid:
                invited.add(uid)
            else:
                unresolved.append("@" + username)
        elif ent.type == "text_link" and getattr(ent, "url", None):
            match = re.search(r"tg://user\?id=(\d+)", ent.url)
            if match:
                invited.add(int(match.group(1)))

    for token in args[2:]:
        token = token.strip().strip(",")
        if token.isdigit():
            invited.add(int(token))
        elif token.startswith("@"):
            uid = resolve_username(message.chat.id, token)
            if uid:
                invited.add(uid)
            elif token not in unresolved:
                unresolved.append(token)

    invited.discard(message.from_user.id)
    if unresolved or len(invited) != extra:
        details = (" Не удалось распознать: " + ", ".join(unresolved) + "." if unresolved else "")
        await message.reply(
            f"Нужно указать ровно {extra} разных приглашённых. Распознано: {len(invited)}.{details}\n"
            "Обычные @username распознаются, если бот уже видел сообщения этих людей в этом чате. "
            "Также можно ответить на сообщение игрока, выбрать Telegram-упоминание или указать ID."
        )
        return
    gid = make_game_id(message.chat.id, message.from_user.id)
    players = {message.from_user.id: message.from_user.full_name}
    game = {
        "chat_id": message.chat.id, "creator": message.from_user.id,
        "limit": extra, "players": players, "invited": invited,
        "alive": [], "order": [message.from_user.id], "phase": "lobby",
        "current_uid": None, "aimed": {}, "dodging": set(),
        "pending_action": {}
    }
    MULTI_DUELS[gid] = game
    await message.answer(
        multi_duel_text(game) + "\n\nПриглашены: " +
        ", ".join(f"<a href='tg://user?id={uid}'>игрок</a>" for uid in invited),
        reply_markup=multi_duel_keyboard(gid, game)
    )


@dp.callback_query(lambda c: (c.data or "").startswith(("mdjoin:", "mdact:", "mdtarget:", "mdcancel:", "mdback:")))
async def multi_duel_callback(call: CallbackQuery):
    parts = call.data.split(":")
    action, gid = parts[0], parts[1]
    game = MULTI_DUELS.get(gid)
    if not game:
        await call.answer("Игра уже завершена.", show_alert=True)
        return
    uid = call.from_user.id

    if action == "mdcancel":
        if uid != game["creator"]:
            await call.answer("Отменить может только создатель.", show_alert=True)
            return
        MULTI_DUELS.pop(gid, None)
        await call.message.edit_text("❌ Коллективная дуэль отменена.")
        await call.answer()
        return

    if action == "mdjoin":
        if game["phase"] != "lobby":
            await call.answer("Набор закрыт.", show_alert=True)
            return
        if uid not in game["invited"]:
            await call.answer("Ты не приглашён в эту дуэль.", show_alert=True)
            return
        if uid in game["players"]:
            await call.answer("Ты уже участвуешь.")
            return
        game["players"][uid] = call.from_user.full_name
        game["order"].append(uid)
        if len(game["players"]) == game["limit"] + 1:
            game["alive"] = list(game["order"])
            game["phase"] = "active"
            game["current_uid"] = game["alive"][0]
        await call.message.edit_text(
            multi_duel_text(game), reply_markup=multi_duel_keyboard(gid, game)
        )
        await call.answer("Ты в игре!")
        return

    if action == "mdact":
        if game["phase"] != "active" or game["current_uid"] != uid:
            await call.answer("Сейчас не твой ход.", show_alert=True)
            return
        mode = parts[2]
        if mode == "dodge":
            game["dodging"].add(uid)
            await multi_duel_advance_turn(call, gid, game, f"🛡 {game['players'][uid]} уклонился и пропустил ход.")
            return
        if mode not in ("aim", "shoot"):
            await call.answer("Неизвестное действие.", show_alert=True)
            return
        if mode == "shoot" and uid not in game["aimed"]:
            await call.answer("Сначала прицелься в игрока.", show_alert=True)
            return
        targets = [x for x in game["alive"] if x != uid]
        if not targets:
            await call.answer("Нет доступных целей.", show_alert=True)
            return
        game["pending_action"][uid] = mode
        rows = [[InlineKeyboardButton(
            text=game["players"][target],
            callback_data=f"mdtarget:{gid}:{target}"
        )] for target in targets]
        rows.append([InlineKeyboardButton(text="↩️ Назад", callback_data=f"mdback:{gid}")])
        await call.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
        await call.answer("Выбери цель.")
        return

    if action == "mdback":
        if game["phase"] == "active" and game["current_uid"] == uid:
            await call.message.edit_reply_markup(reply_markup=multi_duel_keyboard(gid, game))
            await call.answer()
        else:
            await call.answer("Недоступно.", show_alert=True)
        return

    if action == "mdtarget":
        if game["phase"] != "active" or game["current_uid"] != uid:
            await call.answer("Сейчас не твой ход.", show_alert=True)
            return
        target = int(parts[2])
        mode = game["pending_action"].pop(uid, None)
        if target not in game["alive"] or target == uid or mode not in ("aim", "shoot"):
            await call.answer("Это действие недоступно.", show_alert=True)
            return
        if mode == "aim":
            game["aimed"][uid] = target
            await multi_duel_advance_turn(
                call, gid, game, f"🎯 {game['players'][uid]} прицелился в {game['players'][target]}."
            )
            return

        # Выстрел: прицеливание повышает точность; уклонение гарантированно спасает от одного выстрела.
        if target in game["dodging"]:
            game["dodging"].discard(target)
            note = f"💨 {game['players'][target]} уклонился от выстрела {game['players'][uid]}!"
        else:
            hit = random.random() < 0.85
            if hit:
                game["alive"].remove(target)
                game["aimed"].pop(uid, None)
                note = f"💥 {game['players'][uid]} выбил игрока {game['players'][target]}!"
            else:
                note = f"❗ {game['players'][uid]} промахнулся по {game['players'][target]}."
        if len(game["alive"]) == 1:
            winner_id = game["alive"][0]
            MULTI_DUELS.pop(gid, None)
            await call.message.edit_text(
                "🏆 <b>Коллективная дуэль завершена!</b>\n" + note +
                f"\n\nПобедитель: <b>{game['players'][winner_id]}</b>"
            )
            await call.answer("Игра завершена!")
            return
        await multi_duel_advance_turn(call, gid, game, note)
        return


async def multi_duel_advance_turn(call, gid, game, note):
    current_index = game["order"].index(game["current_uid"])
    for offset in range(1, len(game["order"]) + 1):
        candidate = game["order"][(current_index + offset) % len(game["order"])]
        if candidate in game["alive"]:
            game["current_uid"] = candidate
            break
    await call.message.edit_text(
        multi_duel_text(game, note), reply_markup=multi_duel_keyboard(gid, game)
    )
    await call.answer("Ход завершён.")


# ==================== МАФИЯ ====================

MAFIA_GAMES = {}
MAFIA_DISCUSSION_SECONDS = 180
MAFIA_LOBBY_SECONDS = 120
MAFIA_MAX_PLAYERS = 10


def mafia_lobby_text(game):
    names = [mafia_mention(uid, p["name"]) for uid, p in game["players"].items()]
    players_text = "\n".join(f"{i+1}. {name}" for i, name in enumerate(names)) or "Пока никого нет"
    creator = mafia_mention(game["creator_id"], game["creator_name"])
    remaining = max(0, int(game.get("lobby_deadline", 0) - asyncio.get_running_loop().time()))
    return (f"🎭 <b>Новая игра в мафию!</b>\n\n"
            f"Создатель: {creator}\n"
            f"Игроки ({len(game['players'])}/{MAFIA_MAX_PLAYERS}):\n{players_text}\n\n"
            f"Набор: 2 минуты (осталось примерно {remaining} сек.)\n"
            "Для старта нужно минимум 4 игрока.")

def mafia_join_keyboard(chat_id: int, count: int = 0):
    rows = [[InlineKeyboardButton(
        text=f"🎭Зайти в игру ({count}/{MAFIA_MAX_PLAYERS})",
        callback_data=f"mafia_join:{chat_id}"
    )]]
    if count >= 4:
        rows.append([InlineKeyboardButton(text="▶️ Начать игру", callback_data=f"mafia_start:{chat_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def mafia_action_keyboard(chat_id: int, action: str, targets: list):
    rows = []
    for user_id, name in targets:
        rows.append([InlineKeyboardButton(
            text=name[:60],
            callback_data=f"mafia_act:{chat_id}:{action}:{user_id}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def mafia_mention(user_id: int, name: str) -> str:
    safe_name = (name or f"ID {user_id}").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f'<a href="tg://user?id={user_id}">{safe_name}</a>'


def mafia_alive_targets(game, exclude_id=None):
    return [
        (uid, player["name"])
        for uid, player in game["players"].items()
        if player["alive"] and uid != exclude_id
    ]


def mafia_role_distribution(player_count: int):
    # Количество игроков с особыми ролями не превышает количество мирных.
    mafia_count = max(1, (player_count - 4) // 4 + 1)
    sheriff_count = 1 if player_count >= 6 else 0
    doctor_count = 1
    special_count = mafia_count + sheriff_count + doctor_count
    civilian_count = player_count - special_count

    while special_count > civilian_count and mafia_count > 1:
        mafia_count -= 1
        special_count = mafia_count + sheriff_count + doctor_count
        civilian_count = player_count - special_count

    if special_count > civilian_count:
        sheriff_count = 0
        special_count = mafia_count + doctor_count
        civilian_count = player_count - special_count

    return mafia_count, doctor_count, sheriff_count, civilian_count


def mafia_make_roles(player_ids):
    count = len(player_ids)
    mafia_count, doctor_count, sheriff_count, _ = mafia_role_distribution(count)
    roles = (
        ["mafia"] * mafia_count
        + ["doctor"] * doctor_count
        + ["sheriff"] * sheriff_count
        + ["civilian"] * (count - mafia_count - doctor_count - sheriff_count)
    )
    random.shuffle(roles)
    return dict(zip(player_ids, roles))


def mafia_role_title(role):
    return {
        "mafia": "🔪 Мафия",
        "doctor": "🩺 Доктор",
        "sheriff": "⭐ Шериф",
        "civilian": "👤 Мирный житель",
    }.get(role, "Неизвестная роль")


async def mafia_start_night(chat_id: int):
    game = MAFIA_GAMES.get(chat_id)
    if not game:
        return
    alive = mafia_alive_targets(game)
    if not alive:
        await mafia_finish(chat_id, "Игра завершена: не осталось игроков.")
        return

    game["phase"] = "night_mafia"
    game["night_choices"] = {}
    game["mafia_choices"] = {}
    game["doctor_choice"] = None
    game["sheriff_choice"] = None

    mafia_ids = [
        uid for uid, player in game["players"].items()
        if player["alive"] and player["role"] == "mafia"
    ]
    targets = mafia_alive_targets(game)
    keyboard = mafia_action_keyboard(chat_id, "kill", targets)

    for uid in mafia_ids:
        try:
            await bot.send_message(
                uid,
                "🌙 <b>Ночь. Твой ход.</b>\nВыбери игрока, которого мафия должна устранить:",
                reply_markup=keyboard
            )
        except Exception:
            await bot.send_message(
                chat_id,
                f"⚠️ Не удалось отправить ночное действие игроку {mafia_mention(uid, game['players'][uid]['name'])}."
            )

    if not mafia_ids:
        await mafia_finish(chat_id, "Ошибка игры: в живых не осталось мафии.")
        return


async def mafia_advance_after_mafia(chat_id: int):
    game = MAFIA_GAMES.get(chat_id)
    if not game or game["phase"] != "night_mafia":
        return
    mafia_ids = [
        uid for uid, player in game["players"].items()
        if player["alive"] and player["role"] == "mafia"
    ]
    if not all(uid in game["mafia_choices"] for uid in mafia_ids):
        return

    counts = {}
    for target_id in game["mafia_choices"].values():
        counts[target_id] = counts.get(target_id, 0) + 1
    max_votes = max(counts.values())
    chosen = random.choice([uid for uid, votes in counts.items() if votes == max_votes])
    game["night_victim"] = chosen
    game["phase"] = "night_doctor"

    doctors = [
        uid for uid, player in game["players"].items()
        if player["alive"] and player["role"] == "doctor"
    ]
    targets = mafia_alive_targets(game)
    keyboard = mafia_action_keyboard(chat_id, "heal", targets)
    for uid in doctors:
        try:
            await bot.send_message(
                uid,
                "🩺 <b>Ход доктора.</b>\nКого вылечить этой ночью? Можно выбрать себя.",
                reply_markup=keyboard
            )
        except Exception:
            pass

    if not doctors:
        await mafia_advance_after_doctor(chat_id)


async def mafia_advance_after_doctor(chat_id: int):
    game = MAFIA_GAMES.get(chat_id)
    if not game or game["phase"] != "night_doctor":
        return
    doctors = [
        uid for uid, player in game["players"].items()
        if player["alive"] and player["role"] == "doctor"
    ]
    if doctors and game["doctor_choice"] is None:
        return

    game["phase"] = "night_sheriff"
    sheriffs = [
        uid for uid, player in game["players"].items()
        if player["alive"] and player["role"] == "sheriff"
    ]
    if not sheriffs:
        await mafia_resolve_night(chat_id)
        return

    targets = mafia_alive_targets(game)
    keyboard = mafia_action_keyboard(chat_id, "check", targets)
    for uid in sheriffs:
        try:
            await bot.send_message(
                uid,
                "⭐ <b>Ход шерифа.</b>\nКого проверить?",
                reply_markup=keyboard
            )
        except Exception:
            pass


async def mafia_resolve_night(chat_id: int):
    game = MAFIA_GAMES.get(chat_id)
    if not game:
        return
    victim = game.get("night_victim")
    healed = game.get("doctor_choice")
    if victim is not None and victim != healed and victim in game["players"]:
        game["players"][victim]["alive"] = False
        result = f"🌅 Наступило утро. Ночью выбыл игрок {mafia_mention(victim, game['players'][victim]['name'])}."
    else:
        result = "🌅 Наступило утро. Этой ночью никто не выбыл."

    await bot.send_message(chat_id, result)
    await mafia_start_discussion(chat_id)


async def mafia_start_discussion(chat_id: int):
    game = MAFIA_GAMES.get(chat_id)
    if not game:
        return
    game["phase"] = "discussion"
    game["votes"] = {}
    game["discussion_task"] = asyncio.create_task(
        mafia_discussion_timer(chat_id, game["round"])
    )
    await bot.send_message(
        chat_id,
        "💬 <b>Обсуждение началось!</b>\n"
        "У вас есть 3 минуты, чтобы обсудить, кто может быть мафией.\n"
        "После обсуждения начнётся голосование."
    )


async def mafia_discussion_timer(chat_id: int, round_number: int):
    try:
        await asyncio.sleep(MAFIA_DISCUSSION_SECONDS)
        game = MAFIA_GAMES.get(chat_id)
        if not game or game["phase"] != "discussion" or game["round"] != round_number:
            return
        await mafia_start_voting(chat_id)
    except asyncio.CancelledError:
        return


async def mafia_start_voting(chat_id: int):
    game = MAFIA_GAMES.get(chat_id)
    if not game:
        return
    game["phase"] = "voting"
    game["votes"] = {}
    alive = mafia_alive_targets(game)
    keyboard = mafia_action_keyboard(chat_id, "vote", alive)
    for uid, player in game["players"].items():
        if not player["alive"]:
            continue
        try:
            await bot.send_message(
                uid,
                "🗳 <b>Голосование!</b>\nВыбери игрока, которого нужно исключить:",
                reply_markup=keyboard
            )
        except Exception:
            pass
    await bot.send_message(chat_id, "🗳 <b>Началось голосование!</b> Проверь личные сообщения бота.")


async def mafia_finish(chat_id: int, reason: str):
    game = MAFIA_GAMES.pop(chat_id, None)
    if not game:
        return
    task = game.get("discussion_task")
    if task and not task.done():
        task.cancel()

    role_lines = []
    for uid, player in game["players"].items():
        role_lines.append(
            f"• {mafia_mention(uid, player['name'])} — <b>{mafia_role_title(player['role'])}</b>"
        )
    await bot.send_message(
        chat_id,
        f"🏁 <b>Игра окончена!</b>\n{reason}\n\n"
        f"🎭 <b>Все роли:</b>\n" + "\n".join(role_lines)
    )


async def mafia_resolve_votes(chat_id: int):
    game = MAFIA_GAMES.get(chat_id)
    if not game or game["phase"] != "voting":
        return
    alive_ids = [uid for uid, p in game["players"].items() if p["alive"]]
    if not all(uid in game["votes"] for uid in alive_ids):
        return

    counts = {}
    for target_id in game["votes"].values():
        counts[target_id] = counts.get(target_id, 0) + 1
    if not counts:
        await bot.send_message(chat_id, "Голосование не состоялось.")
        game["round"] += 1
        await mafia_start_night(chat_id)
        return

    top = max(counts.values())
    winners = [uid for uid, votes in counts.items() if votes == top]
    if len(winners) != 1:
        await bot.send_message(chat_id, "⚖️ Ничья! Никто не выбыл.")
        game["round"] += 1
        await mafia_start_night(chat_id)
        return

    eliminated = winners[0]
    game["players"][eliminated]["alive"] = False
    await bot.send_message(
        chat_id,
        f"⚖️ Голосование завершено. "
        f"{mafia_mention(eliminated, game['players'][eliminated]['name'])} выбыл из игры.\n"
        "Его роль пока не раскрывается."
    )

    if game["players"][eliminated]["role"] == "mafia":
        await mafia_finish(chat_id, "✅ Мирные жители вычислили мафию голосованием!")
        return

    game["round"] += 1
    await mafia_start_night(chat_id)


async def mafia_refresh_lobby(chat_id):
    game = MAFIA_GAMES.get(chat_id)
    if not game or game.get("phase") != "lobby" or not game.get("lobby_message_id"):
        return
    count = len(game["players"])
    markup = mafia_join_keyboard(chat_id, count)
    try:
        # Синхронно обновляем список участников и счётчик на кнопке.
        await bot.edit_message_text(
            text=mafia_lobby_text(game),
            chat_id=chat_id,
            message_id=game["lobby_message_id"],
            reply_markup=markup,
        )
    except Exception as exc:
        # Если текст не изменился, всё равно пробуем обновить клавиатуру.
        try:
            await bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=game["lobby_message_id"],
                reply_markup=markup,
            )
        except Exception as markup_exc:
            logging.warning(
                "Не удалось обновить лобби мафии в чате %s: %s; markup: %s",
                chat_id, exc, markup_exc,
            )

async def mafia_lobby_timeout(chat_id):
    try:
        while True:
            game = MAFIA_GAMES.get(chat_id)
            if not game or game.get("phase") != "lobby": return
            remaining = game.get("lobby_deadline", 0) - asyncio.get_running_loop().time()
            if remaining <= 0: break
            await asyncio.sleep(remaining)
        game = MAFIA_GAMES.get(chat_id)
        if game and game.get("phase") == "lobby":
            MAFIA_GAMES.pop(chat_id, None)
            try:
                await bot.edit_message_text("⌛ Время набора истекло. Игра в мафию не началась.",
                                            chat_id, game["lobby_message_id"], reply_markup=None)
            except Exception: pass
    except asyncio.CancelledError:
        return

@dp.message(Command("mafia_extend"))
@dp.message(Command("mafia_add_time"))
async def cmd_mafia_extend(message: types.Message):
    game = MAFIA_GAMES.get(message.chat.id)
    if not game or game.get("phase") != "lobby":
        await message.reply("Активного набора нет."); return
    if not message.from_user or message.from_user.id != game["creator_id"]:
        await message.reply("Только создатель игры может продлить набор."); return
    task = game.get("lobby_task")
    if task: task.cancel()
    game["lobby_deadline"] = asyncio.get_running_loop().time() + 30
    game["lobby_task"] = asyncio.create_task(mafia_lobby_timeout(chat_id=message.chat.id))
    # Таймер после продления составляет ровно 30 секунд.
    await mafia_refresh_lobby(message.chat.id)
    await message.reply("⏱ Набор продлён ещё на 30 секунд.")

@dp.message(Command("mafia"))
@dp.message(Command("мафия"))
async def cmd_mafia(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        await message.answer("🎭 Создавать игру можно только в группе.")
        return
    chat_id = message.chat.id
    if chat_id in MAFIA_GAMES:
        await message.answer("В этом чате уже есть активная игра или набор в мафию.")
        return

    loop = asyncio.get_running_loop()
    MAFIA_GAMES[chat_id] = {
        "phase": "lobby",
        "creator_id": message.from_user.id,
        "creator_name": message.from_user.full_name,
        "lobby_deadline": loop.time() + MAFIA_LOBBY_SECONDS,
        "lobby_message_id": None,
        "lobby_task": None,
        "players": {message.from_user.id: {"name": message.from_user.full_name, "role": None, "alive": True}},
        "round": 1,
        "votes": {},
        "mafia_choices": {},
        "doctor_choice": None,
        "sheriff_choice": None,
        "discussion_task": None,
    }
    lobby_msg = await message.answer(
        mafia_lobby_text(MAFIA_GAMES[chat_id]),
        reply_markup=mafia_join_keyboard(chat_id, len(MAFIA_GAMES[chat_id]["players"]))
    )
    MAFIA_GAMES[chat_id]["lobby_message_id"] = lobby_msg.message_id
    MAFIA_GAMES[chat_id]["lobby_task"] = asyncio.create_task(mafia_lobby_timeout(chat_id))


@dp.callback_query(lambda c: (c.data or "").startswith("mafia_join:"))
async def mafia_join_callback(call: CallbackQuery):
    try:
        chat_id = int(call.data.split(":")[1])
    except (ValueError, IndexError):
        await call.answer("Некорректная игра.", show_alert=True)
        return
    game = MAFIA_GAMES.get(chat_id)
    if not game or game["phase"] != "lobby":
        await call.answer("Набор уже закрыт.", show_alert=True)
        return
    if call.from_user.id in game["players"]:
        await call.answer("Ты уже в игре."); return
    if len(game["players"]) >= MAFIA_MAX_PLAYERS:
        await call.answer("Набор заполнен (10/10).", show_alert=True); return
    if asyncio.get_running_loop().time() >= game.get("lobby_deadline", 0):
        await call.answer("Время набора истекло.", show_alert=True); return

    game["players"][call.from_user.id] = {
        "name": call.from_user.full_name,
        "role": None,
        "alive": True,
    }
    count = len(game["players"])
    await mafia_refresh_lobby(chat_id)
    await call.answer(f"Ты в игре! Игроков: {count}/10")


@dp.callback_query(lambda c: (c.data or "").startswith("mafia_start:"))
async def mafia_start_callback(call: CallbackQuery):
    try:
        chat_id = int(call.data.split(":")[1])
    except (ValueError, IndexError):
        await call.answer("Некорректная игра.", show_alert=True)
        return
    game = MAFIA_GAMES.get(chat_id)
    if not game or game["phase"] != "lobby":
        await call.answer("Игра уже запущена или закрыта.", show_alert=True)
        return
    if call.from_user.id != game["creator_id"]:
        await call.answer("Начать игру может только её создатель.", show_alert=True); return
    if len(game["players"]) < 4:
        await call.answer("Нужно минимум 4 игрока.", show_alert=True)
        return
    if game.get("lobby_task"): game["lobby_task"].cancel()

    player_ids = list(game["players"])
    roles = mafia_make_roles(player_ids)
    for uid, role in roles.items():
        game["players"][uid]["role"] = role

    # Роли рассылаются автоматически сразу после старта — отдельной кнопки нет.
    failed = []
    for uid, role in roles.items():
        try:
            await bot.send_message(
                uid,
                f"🎭 <b>Игра в мафию началась!</b>\n\n"
                f"Твоя роль: <b>{mafia_role_title(role)}</b>\n\n"
                + (
                    "Твоя задача — устранить мирных жителей. Выбирай цель ночью."
                    if role == "mafia" else
                    "Твоя задача — помочь мирным жителям вычислить мафию."
                )
            )
        except Exception:
            failed.append(uid)

    if failed:
        MAFIA_GAMES.pop(chat_id, None)
        await call.message.edit_text(
            "❌ Не удалось отправить роль одному или нескольким игрокам.\n"
            "Каждый участник должен открыть личный чат с ботом и нажать /start.\n"
            "Создайте игру заново после этого."
        )
        await call.answer("Не всем удалось доставить роль.", show_alert=True)
        return

    game["phase"] = "starting"
    await call.message.edit_text(
        f"🎭 <b>Игра началась!</b>\n"
        f"Участников: {len(player_ids)}\n"
        "Роли автоматически отправлены каждому игроку в личные сообщения."
    )
    await call.answer("Игра началась!")
    await mafia_start_night(chat_id)


@dp.callback_query(lambda c: (c.data or "").startswith("mafia_act:"))
async def mafia_action_callback(call: CallbackQuery):
    parts = (call.data or "").split(":")
    if len(parts) != 4:
        await call.answer("Ошибка действия.", show_alert=True)
        return
    try:
        chat_id = int(parts[1])
        target_id = int(parts[3])
    except ValueError:
        await call.answer("Ошибка действия.", show_alert=True)
        return
    action = parts[2]
    game = MAFIA_GAMES.get(chat_id)
    if not game:
        await call.answer("Игра уже завершена.", show_alert=True)
        return

    uid = call.from_user.id
    player = game["players"].get(uid)
    target = game["players"].get(target_id)
    if not player or not player["alive"] or not target or not target["alive"]:
        await call.answer("Это действие недоступно.", show_alert=True)
        return
    if uid == target_id and action != "heal":
        await call.answer("Нельзя выбрать себя.", show_alert=True)
        return

    if action == "kill":
        if game["phase"] != "night_mafia" or player["role"] != "mafia":
            await call.answer("Сейчас ты не можешь это сделать.", show_alert=True)
            return
        if uid in game["mafia_choices"]:
            await call.answer("Ты уже выбрал цель.", show_alert=True)
            return
        game["mafia_choices"][uid] = target_id
        await call.answer("Цель выбрана.")
        await mafia_advance_after_mafia(chat_id)
        return

    if action == "heal":
        if game["phase"] != "night_doctor" or player["role"] != "doctor":
            await call.answer("Сейчас ты не можешь это сделать.", show_alert=True)
            return
        if game["doctor_choice"] is not None:
            await call.answer("Ты уже выбрал, кого лечить.", show_alert=True)
            return
        game["doctor_choice"] = target_id
        await call.answer("Игрок выбран для лечения.")
        await mafia_advance_after_doctor(chat_id)
        return

    if action == "check":
        if game["phase"] != "night_sheriff" or player["role"] != "sheriff":
            await call.answer("Сейчас ты не можешь это сделать.", show_alert=True)
            return
        if game["sheriff_choice"] is not None:
            await call.answer("Ты уже проверил игрока этой ночью.", show_alert=True)
            return
        game["sheriff_choice"] = target_id
        if target["role"] == "mafia":
            await call.answer("Ты нашёл мафию!", show_alert=True)
            await mafia_finish(chat_id, "⭐ Шериф обнаружил мафию! Победа мирных жителей.")
            return
        await call.answer("Это не мафия.", show_alert=True)
        await bot.send_message(uid, "🔎 Проверка завершена: выбранный игрок не мафия.")
        await mafia_resolve_night(chat_id)
        return

    if action == "vote":
        if game["phase"] != "voting":
            await call.answer("Сейчас голосование не идёт.", show_alert=True)
            return
        if uid in game["votes"]:
            await call.answer("Ты уже проголосовал.", show_alert=True)
            return
        game["votes"][uid] = target_id
        await call.answer("Голос принят.")
        await bot.send_message(uid, "🗳 Твой голос учтён.")
        await mafia_resolve_votes(chat_id)
        return

    await call.answer("Неизвестное действие.", show_alert=True)


@dp.message(Command("mafia_cancel"))
async def cmd_mafia_cancel(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        return
    game = MAFIA_GAMES.get(message.chat.id)
    if not game:
        await message.answer("Активной игры нет.")
        return
    if game["phase"] != "lobby":
        await message.answer("Отменить уже начавшуюся игру этой командой нельзя."); return
    if not message.from_user or message.from_user.id != game["creator_id"]:
        await message.answer("Только создатель может отменить набор."); return
    if game.get("lobby_task"): game["lobby_task"].cancel()
    MAFIA_GAMES.pop(message.chat.id, None)
    await message.answer("Игра в мафию отменена.")



# ==================== ОБЩИЙ ФИЛЬТР ====================

@dp.message()
async def filter_messages(message: types.Message):
    if message.business_connection_id:
        return

    if message.from_user:
        cache_user(message.chat.id, message.from_user)
    if message.reply_to_message and message.reply_to_message.from_user:
        cache_user(message.chat.id, message.reply_to_message.from_user)
    if message.new_chat_members:
        for u in message.new_chat_members:
            cache_user(message.chat.id, u)

    if SERVICE_CLEANER_ENABLED.get(message.chat.id, True) and is_service_message(message):
        try:
            await message.delete()
        except Exception as e:
            print(f"Не удалил сервисное: {e}")
        return

    # Во время мафии писать могут только живые участники и только в фазе обсуждения.
    mafia_game = MAFIA_GAMES.get(message.chat.id)
    if mafia_game and mafia_game.get("phase") != "lobby":
        uid = message.from_user.id if message.from_user else None
        participant = mafia_game["players"].get(uid) if uid is not None else None
        can_write = (
            mafia_game.get("phase") == "discussion"
            and participant is not None
            and participant.get("alive", False)
        )
        if not can_write:
            try:
                await message.delete()
            except Exception as e:
                print(f"Не удалось удалить сообщение во время мафии: {e}")
            return

    if not message.text:
        return
    if message.text.startswith("/"):
        return

    low = message.text.strip().lower()
    low_clean = low.strip("?!.,;: ")
    if low_clean in (
        "кто ты", "кто это", "who are you", "who r u",
        "кто ты такой", "кто ты такая", "чё ты", "че ты",
    ):
        user_id, name, err = await resolve_target(message)
        if err:
            user_id, name = None, None
        text = await build_stats_message(message, user_id, name)
        try:
            await message.answer(text)
        except Exception:
            pass
        return

    if CAPS_ENABLED.get(message.chat.id, False) and is_caps_lock(message.text):
        try:
            await message.delete()
            print(f"Удалён капслок от {message.from_user.id} в {message.chat.id}")
        except Exception as e:
            print(f"Не удалил капслок: {e}")
        return

    if LINKS_ENABLED.get(message.chat.id, False) and has_forbidden_links(message.text):
        try:
            await message.delete()
            print(f"Удалена ссылка от {message.from_user.id} в {message.chat.id}")
        except Exception as e:
            print(f"Не удалил ссылку: {e}")
        return

    if not CENSOR_ENABLED.get(message.chat.id, True):
        track_message(message.chat.id, message.from_user, is_bad=False)
        return

    is_bad = has_bad_words(message.text)

    if is_bad:
        try:
            await message.delete()
            print(f"Удалено от {message.from_user.id} в {message.chat.id}")
        except Exception as e:
            print(f"Не удалил мат: {e}")
        return

    track_message(message.chat.id, message.from_user, is_bad=False)


# ==================== РЕГИСТРАЦИЯ ====================

async def set_commands():
    commands = [
        types.BotCommand(command="start", description="Запустить бота"),
        types.BotCommand(command="help", description="Все команды"),
        types.BotCommand(command="everyone", description="Созвать всех"),
        types.BotCommand(command="rps", description="КНБ с ботом или @user"),
        types.BotCommand(command="duel", description="Вызвать на дуэль"),
        types.BotCommand(command="dice", description="Кубик"),
        types.BotCommand(command="coin", description="Орёл/решка"),
        types.BotCommand(command="ball", description="Магический шар"),
        types.BotCommand(command="mafia", description="Создать игру в мафию"),
        types.BotCommand(command="stats", description="Статистика пользователя"),
        types.BotCommand(command="whoareyou", description="Кто этот пользователь"),
        types.BotCommand(command="delete", description="Удалить (reply)"),
        types.BotCommand(command="censor", description="Вкл. цензуру"),
        types.BotCommand(command="uncensor", description="Выкл. цензуру"),
        types.BotCommand(command="censor_status", description="Статус цензуры"),
        types.BotCommand(command="caps", description="Вкл. защиту от капслока"),
        types.BotCommand(command="uncaps", description="Выкл. защиту от капслока"),
        types.BotCommand(command="caps_status", description="Статус защиты от капслока"),
        types.BotCommand(command="links", description="Вкл. защиту от ссылок"),
        types.BotCommand(command="unlinks", description="Выкл. защиту от ссылок"),
        types.BotCommand(command="links_status", description="Статус защиты от ссылок"),
        types.BotCommand(command="service_on", description="Вкл. чистку"),
        types.BotCommand(command="service_off", description="Выкл. чистку"),
        types.BotCommand(command="service_status", description="Статус чистки"),
        types.BotCommand(command="users", description="Кого знает бот"),
        types.BotCommand(command="kick", description="Кик"),
        types.BotCommand(command="ban", description="Бан"),
        types.BotCommand(command="unban", description="Разбан"),
        types.BotCommand(command="tempban", description="Врембан"),
        types.BotCommand(command="mute", description="Мут"),
        types.BotCommand(command="vmute", description="Мут голосовых"),
        types.BotCommand(command="unmute", description="Размут"),
        types.BotCommand(command="promote", description="Назначить админом"),
        types.BotCommand(command="demote", description="Снять с админки"),
        types.BotCommand(command="addsuper", description="Добавить супер-админа"),
        types.BotCommand(command="delsuper", description="Убрать супер-админа"),
        types.BotCommand(command="superlist", description="Список супер-админов"),
    ]
    try:
        await bot.set_my_commands(commands)
    except Exception as e:
        print(f"set_my_commands: {e}")


# ==================== ЗАПУСК ====================

async def main():
    global BOT_ID
    print("=== MAIN START ===")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        print(f"delete_webhook: {e}")

    me = await bot.get_me()
    BOT_ID = me.id
    print(f"Бот: @{me.username} (id={BOT_ID})")
    print(f"Супер-админы (username): {SUPER_ADMINS}")
    print(f"Супер-админы (id): {SUPER_ADMIN_IDS}")

    await set_commands()
    print("=== BOT STARTED, POLLING ===")

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        print(f"Polling упал: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
