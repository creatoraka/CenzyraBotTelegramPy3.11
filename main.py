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
RPS_INVITES = {}
CENSOR_ENABLED = {}
USERNAME_CACHE = {}
USER_ID_TO_NAME = {}
SERVICE_CLEANER_ENABLED = {}

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

# Только реальные матерные корни. Без общеупотребительных слов.
LONG_BAD = [
    # хуй
    "хуесос", "хуеплет", "хуеглот", "хуемраз",
    # пизд
    "пизда", "пизде", "пизду", "пизды", "пиздо",
    "пиздец", "пиздану", "пиздато", "пиздатый",
    "пиздюк", "пиздюл", "пиздюх",
    "пиздобол", "пиздабол", "пиздоболка",
    "пиздрик", "пиздрила", "пиздренок",
    "пиздюлина", "пиздюлей", "пиздюли",
    "распизд", "запизд", "впизд", "спизд", "испизд",
    "напизд", "пропизд", "припизд", "допизд",
    # бля
    "блядина", "блядинк", "блядищ",
    "блядство", "блядств", "блядск", "блядская",
    "блядун", "блядуш",
    "блядва", "блядво",
    "забляд", "набляд", "пробляд",
    "выбляд", "выблядок",
    "добляд", "прибляд",
    # еб
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
    # сук
    "сучка", "сучки", "сучонок",
    "сучара", "сучарк", "сучий", "сучья",
    # муд
    "мудак", "мудачь",
    "мудил", "мудила", "мудило",
    "мудозвон",
    "мудень", "мудня",
    "замуд", "намуд", "промуда",
    # пидор
    "пидор", "пидар", "пидер",
    "педик", "педер", "педераст",
    "пидорас", "пидарас", "пидорасина",
    "пидорств", "пидарств",
    "пидорок",
    # гандон
    "гандон", "гондон",
    "кондом",
    # прочее
    "паскуд", "паскудник",
    "падлюк", "падлюка", "падлючк",
    "гомик", "гомосек",
    "залупка", "залупок",
    "мандавошк", "мандав", "мандуй",
    # шлюх
    "шлюха", "шлюхи", "шлюхо", "шлюхе", "шлюху",
    "шлюшка", "шлюшки", "шлюшк", "шлюшонок", "шлюшня",
    "пошлюх",
    "проститут", "проститух",
    "шалава", "шалавы", "шалавищ",
    "потаскух", "потаскушк",
    "хабалка", "хабалк",
    # остальное
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

# Короткие корни — только как отдельные слова
SHORT_BAD = [
    # хуй
    "хуй", "хуя", "хую", "хуе", "хуи", "хуйн",
    "хуйло", "хуйня", "хуец", "хуищ", "хуяч", "хуяр",
    "хуел", "хуею", "хуев",
    "схуя", "схуй",
    # хер
    "хер",
    # пизд
    "пизд", "пизж",
    # бля — все формы
    "блядь", "бляди", "блядо", "бляде", "бляду",
    "блять", "блят", "бляд", "бля",
    # еб
    "еб", "ебу", "еби",
    # сука
    "сука", "суки", "суке", "суку", "сукой", "сучар", "сучк",
    "суч", "засук",
    # муд
    "мудор",
    # гандон
    "ганд",
    # пидор
    "пидр",
    # гомо
    "гомо",
    # манда
    "манда", "манде", "манду", "манды", "мандо",
    # шлюх
    "шлюх", "шлюш",
    "шлюха", "шлюхи", "шлюхе", "шлюху", "шлюхой",
    # шалав, потаск, хабал
    "шалав", "потаск", "хабал", "стерв",
    "курв", "курва", "курвы", "курво",
    # блуд
    "блуд",
    # вагин, сперм
    "вагин", "вагина",
    "сперм", "сперма",
    # яичк
    "яичк",
    # срак, срал, срач
    "срак",
    "сру", "срал",
    "срач", "срачь",
    # сса
    "ссат", "ссал", "ссан", "ссани",
    "ссик", "ссику",
    # перд, бзд
    "перд", "пердну", "бзд",
    # вонюч
    "вонюч",
    # моча
    "моча", "мочит", "мочен",
    # жоп
    "жоп",
    # анал
    "анал",
    # анус
    "анус",
    # дроч
    "дроч",
    # онан
    "онан",
    # фелл
    "фелл",
    # орал
    "орал",
    # секс
    "секс", "секса", "сексу", "сексе",
    # снош
    "снош",
    # трах
    "трах", "трахн",
    # шмар
    "шмар",
    # нации
    "кацап", "жид",
    "чурка", "чурки", "чурк",
    "хач", "хачи",
    "азерб", "узбек", "немч", "наци",
    # наркота
    "нарк", "нарко", "торч",
    # оружие/тема
    "бомб", "бомба", "игил",
    # педо
    "педо",
    # оскорбления короткие
    "мраз", "твар",
    "урод", "уроды", "уродина",
    "дрян", "дрянь", "дрянн",
    "подлец",
    "поган",
    "хам", "хамл", "хамск",
    "наглец", "нагл",
    "нахал", "наха",
    # залупа
    "залупа", "залупе", "залупу", "залупы", "залупой",
    # угрозы (только явные)
    "убью",
    "порву", "порвать",
    "сожгу", "сжечь",
]

# Whitelist — обычные слова, которые могут содержать "опасные" корни.
WHITELIST_RAW = {
    # херсон / хер
    "херсон", "херсонес", "херсонский", "херсонская", "херсонский",
    # мандарин
    "мандарин", "мандарины", "мандаринка", "мандаринка",
    "мандариновый", "мандаринчик", "мандаринчики",
    # анализ
    "анализ", "анализа", "анализу", "анализом", "анализе",
    "аналитик", "аналитика", "аналитики", "аналитику",
    "анализировать", "анализировал", "анализирую",
    "аналог", "аналога", "аналогия", "аналогичный", "аналогично",
    "аналоговый",
    # трахея
    "трахея", "трахеи", "трахею", "трахеей", "трахеит",
    "трахеотомия", "трахеостомия",
    # секс / секстант
    "секстант", "секстанта", "секстанты",
    "секция", "секции", "секцию", "секций", "секционный",
    "секрет", "секрета", "секретный", "секретно",
    "секретарь", "секретариат",
    # сук
    "сукаленок", "сукаленка",
    "сукно", "сукна", "сукном", "сукне",
    "суккулент", "суккуленты",
    "сукровица",
    # сракозябра
    "сракозябра", "сракозябры",
    # полов
    "половой", "половая", "половое", "половые", "половых",
    "половинка", "половина", "половину", "половины",
    "половник", "половники",
    # орал
    "оральный", "оральная", "оральное", "оральные",
    "орал", "орала", "орали", "орать",
    # снош
    "сношение", "сношения", "сношению", "сношением",
    "сносно", "сносный", "сносная", "сносное", "сносные",
    "сноска", "сноски", "сноску",
    # дешевк
    "дешевка", "дешевки", "дешевке", "дешевку", "дешевкой",
    "дешевле", "дешевый", "дешевая", "дешево",
    # соль
    "соль", "соли", "солью",
    "соленый", "соленая", "соленое",
    "солнечный", "солнечная", "солнце",
    # анальный
    "анальный", "анальная", "анальное", "анальные",
    # вагина / клитор
    "вагина", "вагины", "вагине", "вагину", "вагиной",
    "вагинальный", "вагинальная",
    "клитор", "клитора", "клиторе", "клитору", "клитором",
    "клиторальный",
    # фаллос / пенис
    "фаллос", "фаллоса", "фаллосу", "фаллосом",
    "пенис", "пениса", "пенису", "пенисом",
    "пенистый", "пенистая",
    # секс
    "сексуальный", "сексуальная", "сексуальное", "сексуальные",
    "сексуальность", "сексуально",
    # мастурбация
    "мастурбация", "мастурбации", "мастурбацию",
    # наркотик
    "наркотик", "наркотики", "наркотика", "наркотиков",
    "наркоз", "наркоза", "наркозный",
    # хамство
    "хамство", "хамства", "хамству", "хамством",
    # поганец
    "поганец", "поганка", "поганки",
    "поганый", "поганая", "поганое", "поганые",
    # трава
    "трава", "травы", "траве", "траву", "травой", "травам", "травах",
    "травинка", "травинки", "травинку",
    "травля", "травли", "травлю",
    "травма", "травмы", "травме", "травму", "травмой",
    "травматолог", "травматология",
    "траверс", "траверса",
    # лупа
    "лупа", "лупы", "лупе", "лупу", "лупой",
    "лупить", "луплю", "лупит",
    # муравей
    "муравей", "муравья", "муравью", "муравьи", "муравьёв", "муравьев",
    "муравьиный", "муравьиная", "муравейник", "муравейника",
    # суккулент
    "суккулент", "суккуленты", "суккулентный",
}

WHITELIST = {normalize(w) for w in WHITELIST_RAW}


def has_bad_words(text: str) -> bool:
    """
    Логика:
    1. Разбиваем текст на слова. Каждое нормализуем.
    2. Длинные корни — подстрокой в слове.
    3. Короткие корни — точное совпадение со словом.
    4. Обход "б л я т ь" (все слова ≤2 букв) — склеиваем и ищем.
    5. Обход "б-л-я-т-ь" (без пробелов) — склеиваем и ищем.
    """
    if not text:
        return False

    raw_words = re.findall(r"[A-Za-zА-Яа-яЁё0-9]+", text)
    norm_words = [normalize(w) for w in raw_words if normalize(w)]

    if not norm_words:
        return False

    # Если весь текст — одно whitelist-слово → не мат
    if len(norm_words) == 1 and norm_words[0] in WHITELIST:
        return False

    # 1) длинные корни — подстрокой
    for w in norm_words:
        if w in WHITELIST:
            continue
        for bad in LONG_BAD:
            if bad in w:
                return True

    # 2) короткие — точное совпадение со словом
    for w in norm_words:
        if w in WHITELIST:
            continue
        if w in SHORT_BAD:
            return True

    # 3) обход "б л я т ь" — все слова короткие
    all_short = all(len(w) <= 2 for w in norm_words)
    if all_short and len(norm_words) >= 2:
        flat = normalize(text)
        if flat and flat not in WHITELIST:
            for bad in SHORT_BAD:
                if len(bad) >= 3 and bad in flat:
                    return True
            for bad in LONG_BAD:
                if bad in flat:
                    return True

    # 4) обход "б-л-я-т-ь" — без пробелов вообще
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
                    "Или используй reply / числовой ID."
                )

    username = extract_username_from_text(text)
    if username:
        uid = resolve_username(chat_id, username)
        if uid:
            return uid, get_name(chat_id, uid), None
        return None, username, (
            f"❌ Не удалось найти <code>{username}</code> в кэше чата."
        )

    uid = extract_user_id_from_text(text)
    if uid:
        return uid, f"ID {uid}", None

    return None, None, (
        "❌ Укажи пользователя:\n"
        "• ответь (reply) на его сообщение\n"
        "• укажи @username (если писал в чате)\n"
        "• укажи числовой ID"
    )


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


async def bot_can_restrict(message: types.Message) -> bool:
    try:
        me = await bot.get_me()
        member = await bot.get_chat_member(message.chat.id, me.id)
        return bool(getattr(member, "can_restrict_members", False))
    except Exception as e:
        logging.warning(f"bot_can_restrict: {e}")
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
    if await is_target_admin(message, user_id):
        await message.reply(f"🛡 <b>{name}</b> — админ. Его нельзя наказать.")
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
        "📢 Созываю всех через /everyone\n"
        "🎲 Развлекательные команды\n"
        "🔨 Модерация\n\n"
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
        "• /dice — бросить кубик (1–6)\n"
        "• /coin — орёл или решка\n"
        "• /ball &lt;вопрос&gt; — магический шар\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📢 <b>Общее:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "• /everyone — созвать всех участников\n\n"
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
        "• /unmute — снять мут\n\n"
        "<b>Управление ботом:</b>\n"
        "• /censor — включить цензуру\n"
        "• /uncensor — выключить цензуру\n"
        "• /censor_status — статус цензуры\n"
        "• /service_on — вкл. чистку сервисных\n"
        "• /service_off — выкл. чистку\n"
        "• /service_status — статус чистки\n\n"
        "💡 <i>Все команды администрации работают только для админов чата.</i>"
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


# ==================== /everyone ====================

@dp.message(Command("everyone"))
@dp.message(Command("все"))
async def cmd_everyone(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        return
    if not await is_admin(message):
        await message.reply("❌ Только админы могут созывать всех.")
        return

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
        logging.warning(f"get_chat_administrators: {e}")

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


# ==================== /delete ====================

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
        logging.warning(f"delete target: {e}")
    try:
        await message.delete()
    except Exception as e:
        logging.warning(f"delete cmd: {e}")


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
    ]])


def rps_invite_keyboard(invite_id):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Принять", callback_data=f"rpsi:{invite_id}:yes"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"rpsi:{invite_id}:no"),
    ]])


def make_game_id(chat_id, user_id):
    return f"{chat_id}_{user_id}_{random.randint(100000, 999999)}"


@dp.message(Command("rps"))
@dp.message(Command("кнб"))
async def cmd_rps(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        await message.reply("❌ Только в группах.")
        return

    cache_user(message.chat.id, message.from_user)

    target_id, target_name = await resolve_target_for_rps(message)

    # Игра с ботом
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

    # PvP — приглашение
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


@dp.callback_query()
async def rps_callback(call: CallbackQuery):
    # ---- приглашение ----
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
                    f"отклонил приглашение от {invite['from_mention']}."
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

    # ---- сама игра ----
    if call.data.startswith("rps:"):
        parts = call.data.split(":")
        if len(parts) != 3:
            await call.answer("Ошибка.", show_alert=True)
            return

        _, game_id, choice = parts
        game = RPS_GAMES.get(game_id)
        if not game:
            await call.answer("Игра не найдена.", show_alert=True)
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
            try:
                await call.message.edit_text(
                    f"🎮 <b>КНБ</b>\n\n"
                    f"👤 {RPS_CHOICES[choice]}\n🤖 {RPS_CHOICES[bot_choice]}\n\n"
                    f"<b>{verdict}</b>"
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

        # Проверка хода
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
            try:
                await call.message.edit_text(
                    f"🎮 <b>КНБ результат</b>\n\n"
                    f"👤 {game['a_mention']}: {RPS_CHOICES[ca]}\n"
                    f"👤 {game['b_mention']}: {RPS_CHOICES[cb]}\n\n"
                    f"<b>{verdict}</b>"
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
        await message.reply("❌ Укажи минуты: /mute 15")
        return
    try:
        until_ts = int((datetime.now() + timedelta(minutes=minutes)).timestamp())
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=user_id,
            permissions=types.ChatPermissions(can_send_messages=False),
            until_date=until_ts
        )
        await message.answer(f"🔇 {name} замучен на <b>{minutes} мин.</b>")
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
            permissions=types.ChatPermissions(
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
        await message.answer(f"🔊 {name} размучен.")
    except Exception as e:
        await message.reply(f"❌ {e}")


# ==================== ОБЩИЙ ФИЛЬТР ====================

@dp.message()
async def filter_messages(message: types.Message):
    if message.from_user:
        cache_user(message.chat.id, message.from_user)
    if message.reply_to_message and message.reply_to_message.from_user:
        cache_user(message.chat.id, message.reply_to_message.from_user)

    if SERVICE_CLEANER_ENABLED.get(message.chat.id, True) and is_service_message(message):
        try:
            await message.delete()
        except Exception as e:
            logging.warning(f"Не удалил сервисное: {e}")
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
            logging.info(f"Удалено от {message.from_user.id} в {message.chat.id}")
        except Exception as e:
            logging.warning(f"Не удалил мат: {e}")


# ==================== РЕГИСТРАЦИЯ ====================

async def set_commands():
    commands = [
        types.BotCommand(command="start", description="Запустить бота"),
        types.BotCommand(command="help", description="Все команды"),
        types.BotCommand(command="everyone", description="Созвать всех"),
        types.BotCommand(command="rps", description="КНБ с ботом или @user"),
        types.BotCommand(command="dice", description="Кубик"),
        types.BotCommand(command="coin", description="Орёл/решка"),
        types.BotCommand(command="ball", description="Магический шар"),
        types.BotCommand(command="delete", description="Удалить (reply)"),
        types.BotCommand(command="censor", description="Вкл. цензуру"),
        types.BotCommand(command="uncensor", description="Выкл. цензуру"),
        types.BotCommand(command="censor_status", description="Статус цензуры"),
        types.BotCommand(command="service_on", description="Вкл. чистку"),
        types.BotCommand(command="service_off", description="Выкл. чистку"),
        types.BotCommand(command="service_status", description="Статус чистки"),
        types.BotCommand(command="kick", description="Кик"),
        types.BotCommand(command="ban", description="Бан"),
        types.BotCommand(command="unban", description="Разбан"),
        types.BotCommand(command="tempban", description="Врембан"),
        types.BotCommand(command="mute", description="Мут"),
        types.BotCommand(command="unmute", description="Размут"),
    ]
    try:
        await bot.set_my_commands(commands)
    except Exception as e:
        logging.warning(f"set_my_commands: {e}")


# ==================== ЗАПУСК ====================

async def main():
    global BOT_ID
    logging.info("Запуск бота...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        logging.warning(f"delete_webhook: {e}")

    me = await bot.get_me()
    BOT_ID = me.id
    logging.info(f"Бот: @{me.username} (id={BOT_ID})")

    await set_commands()
    logging.info("Бот запущен, начинаю polling...")

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Polling упал: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
