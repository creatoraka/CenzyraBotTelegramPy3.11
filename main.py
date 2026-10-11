import os
import re
import random
import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
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

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

TEMP_BANS = {}
TEMP_MUTES = {}
RPS_GAMES = {}  # {game_id: {...}}

# ==================== СПИСКИ ЗАПРЕЩЁННЫХ СЛОВ ====================

MAT_ROOTS = [
    r"хуй", r"хуя", r"хую", r"хуе", r"хуё", r"хуи", r"хуйн",
    r"хуйло", r"хуйня", r"хуец", r"хуищ", r"хуяч", r"хуяр",
    r"хуел", r"хуею", r"хуев", r"хуёв",
    r"хуесос", r"хуисос", r"хуеплёт", r"хуеплет",
    r"хуеглёт", r"хуеглот", r"хуемразь",
    r"схуя", r"схуй",
    r"хер", r"херов", r"херня", r"херовина",
    r"пизд", r"пизж",
    r"пизда", r"пизде", r"пизду", r"пизды", r"пиздо", r"пиздё",
    r"пиздану", r"пиздато", r"пиздатый",
    r"пиздец", r"пиздеца", r"пиздецки",
    r"пиздюк", r"пиздюл", r"пиздюх",
    r"пиздобол", r"пиздабол", r"пиздоболка",
    r"пиздопляс", r"пиздостра",
    r"пиздрик", r"пиздрила", r"пиздрёнок",
    r"пиздюлина", r"пиздюлей", r"пиздюли",
    r"распизд", r"запизд", r"впизд", r"спизд", r"испизд",
    r"напизд", r"пропизд", r"припизд", r"допизд",
    r"бляд", r"блят", r"бля",
    r"блядь", r"бляди", r"блядо", r"бляде", r"бляду",
    r"блядство", r"блядств", r"блядск", r"блядская",
    r"блядун", r"блядуш",
    r"блядва", r"блядво",
    r"забляд", r"набляд", r"пробляд",
    r"выбляд", r"выблядок",
    r"добляд", r"прибляд",
    r"еб[аеёиуо]", r"ёб[аеёиуо]",
    r"ебан", r"ёбан", r"ебану", r"ебанут", r"ебанул",
    r"ебат", r"ебать", r"ёбат", r"ёбать", r"ебал", r"ёбал",
    r"ебало", r"ёбало", r"ебальник", r"ебальн",
    r"ебарь", r"ёбарь", r"ебари",
    r"ебуч", r"ёбуч", r"ебучий", r"ёбучий",
    r"ебёт", r"ебет", r"ебётся",
    r"еби", r"ебить", r"ебитв", r"ебитва",
    r"ебля", r"ёбля", r"ебли", r"ёбли",
    r"ебло", r"ёбло", r"еблом",
    r"еблан", r"ёблан", r"ебланк",
    r"ебств", r"ёбств", r"ебу", r"ебусь", r"ебут",
    r"ебак", r"ебака",
    r"заеб", r"заёб", r"заебал", r"заебись", r"заебу",
    r"заебан", r"заёбан",
    r"наеб", r"наёб", r"наебал", r"наебать", r"наебут",
    r"наебан", r"наёбан", r"наебка",
    r"отъеб", r"отъёб", r"отъебал", r"отъебать",
    r"отъебис", r"отъебись",
    r"подъеб", r"подъёб", r"подъебал", r"подъебка",
    r"подъебну", r"подъёбну",
    r"уеб", r"уёб", r"уебал", r"уебать", r"уебан",
    r"уёбан", r"уебищ", r"уёбищ",
    r"въеб", r"въёб", r"въебал", r"въебать", r"въебну",
    r"проеб", r"проёб", r"проебал", r"проебать",
    r"проебан", r"проёбан", r"проебу",
    r"разъеб", r"разъёб", r"разъебал", r"разъебать",
    r"разъебан", r"разъёбан",
    r"съеб", r"съёб", r"съебал", r"съебать", r"съебался",
    r"съебис", r"съебись",
    r"доеб", r"доёб", r"доебал", r"доебать",
    r"доебис", r"доебись",
    r"долбоеб", r"долбоёб", r"долбаеб", r"долбаёб",
    r"долбоебк", r"долбоёбк",
    r"недоеб", r"недоёб",
    r"перееб", r"переёб", r"переебал", r"переебать",
    r"переебан", r"переёбан", r"переебу",
    r"поеб", r"поёб", r"поебал", r"поебать",
    r"поебен", r"поебень", r"поебон",
    r"поебушк", r"поебух",
    r"ебош", r"ёбош", r"ебалда",
    r"сука", r"суки", r"сук[аеиуо]", r"сучк",
    r"сучка", r"сучки", r"сучонок",
    r"суч", r"сучар", r"сучара", r"сучён",
    r"сучарк", r"сучий", r"сучья",
    r"засук",
    r"паскуд", r"паскудник",
    r"падлюк", r"падлюка", r"падлючк",
    r"подлюк",
    r"мудак", r"мудачь",
    r"мудил", r"мудила", r"мудило",
    r"мудозвон", r"мудор",
    r"мудень", r"мудня",
    r"замуд", r"намуд", r"промуда",
    r"гандон", r"гондон", r"ганд",
    r"кондом",
    r"пидор", r"пидар", r"пидер", r"пидр",
    r"педик", r"педер", r"педераст",
    r"пидорас", r"пидарас", r"пидорасина",
    r"пидорств", r"пидарств",
    r"пидорок",
    r"гомик", r"гомо", r"гомосек",
    r"залуп", r"залупа", r"залупе", r"залупу",
    r"залупк", r"залупок",
    r"манда", r"манде", r"манду", r"манды", r"мандо",
    r"мандавошк", r"мандав", r"мандуй",
    r"шлюх", r"шлюш",
    r"шлюха", r"шлюхи", r"шлюхо", r"шлюхе", r"шлюху",
    r"шлюшка", r"шлюшки", r"шлюшк", r"шлюшонк", r"шлюшня",
    r"пошлюх",
    r"проститут", r"проститух",
    r"блядина", r"блядинк", r"блядищ",
    r"шалав", r"шалава", r"шалавы", r"шалавищ",
    r"потаск", r"потаскух", r"потаскушк",
    r"хабал", r"хабалка", r"хабалк",
    r"стерв", r"стерва", r"стервы", r"стерво",
    r"курв", r"курва", r"курвы", r"курво",
    r"блуд", r"блудниц",
    r"влагалищ", r"вагин", r"вагина",
    r"клитор", r"клиторн",
    r"сперм", r"сперма", r"спермат",
    r"сперматозо", r"сперматозоид",
    r"яичк",
    r"мошонк", r"мошонка",
    r"срак", r"срака", r"сраку", r"сраки",
    r"сру", r"срать", r"срал", r"срала",
    r"срач", r"срача", r"сраче", r"срачь",
    r"ссат", r"ссать", r"ссал", r"ссала", r"ссан",
    r"ссани", r"ссанин",
    r"ссик", r"ссику",
    r"пердёж", r"пердеж", r"перд", r"пердну", r"пердану",
    r"пердун", r"пердунь",
    r"бздёж", r"бздеж", r"бздун",
    r"вонюч",
    r"какашк",
    r"говн", r"говно", r"говна", r"говне", r"говну",
    r"говнюк", r"говнюшк",
    r"говня", r"говнян", r"говняст",
    r"дерьм", r"дерьмо", r"дерьма",
    r"моча", r"мочит", r"мочалк",
    r"мочен",
    r"фекал", r"фекали",
    r"испражн",
    r"экскремен",
    r"жоп", r"жопа", r"жопу", r"жопе", r"жопы",
    r"жопан", r"жопень",
    r"задниц", r"задница", r"задницу",
    r"анал", r"анальн",
    r"анус", r"анусн",
    r"простат", r"простата",
    r"дроч", r"дрочи", r"дрочил", r"дрочить",
    r"дрочер",
    r"онан", r"онанизм", r"онанист",
    r"мастурб", r"мастурбац", r"мастурби",
    r"минет", r"миньет", r"минетч",
    r"кунилингус", r"кунилинг",
    r"фелл", r"фелляц",
    r"орал", r"оральн",
    r"сексуаль", r"сексуальн",
    r"полов", r"половойакт",
    r"совокуп", r"совокуплен",
    r"сношен", r"сношение",
    r"трах", r"трахат", r"трахаю", r"трахал", r"трахать",
    r"трахнул", r"трахн",
    r"шмар", r"шмара", r"шмары",
    r"подзаборн",
    r"дешевк", r"дешевка",
    r"хохол", r"хохлы", r"хохлушк",
    r"москал", r"москаль", r"москаля",
    r"кацап", r"кацапн",
    r"жид", r"жиды", r"жидяр",
    r"чурка", r"чурбан", r"чурки", r"чурк",
    r"чучмек",
    r"хач", r"хачик", r"хачи",
    r"азерб",
    r"армяшк", r"армяшка",
    r"дагест", r"дагестан",
    r"чечен", r"чеченец",
    r"узбек",
    r"китаёз", r"китаеза",
    r"немч", r"немчура",
    r"фашист", r"нацист", r"наци",
    r"гитлер",
    r"рашист", r"рашизм",
    r"ватник",
    r"героин", r"герыч",
    r"кокаин",
    r"амфетамин",
    r"мефедрон",
    r"метамфетамин",
    r"марихуан",
    r"гашиш",
    r"мескалин",
    r"экстази",
    r"закладк", r"закладчик",
    r"нарк", r"нарко", r"наркота", r"наркотик",
    r"наркоман", r"наркоманк",
    r"торч", r"торчок",
    r"ширнут", r"ширнул",
    r"суицид",
    r"самоубий", r"самоубийств",
    r"повесит", r"повешусь", r"повесил",
    r"убит", r"убить", r"убийств", r"убийц",
    r"зареза", r"зарежу",
    r"вскрытвен",
    r"террорист", r"терроризм", r"теракт",
    r"взорв", r"взорвать",
    r"бомб", r"бомба",
    r"джихад",
    r"шахид",
    r"смертник",
    r"игил", r"игилов",
    r"алькаид", r"аль-каид",
    r"талиб",
    r"педофил",
    r"малолетк", r"малолеток",
    r"несовершеннолетн",
    r"сволоч", r"сволочь", r"сволочи",
    r"мраз", r"мразь", r"мрази", r"мразот",
    r"твар", r"тварь", r"твари", r"тварюг",
    r"ублюд", r"ублюдок", r"ублюдки",
    r"кретин", r"кретинк",
    r"дебил", r"дебильн",
    r"идиот", r"идиотк",
    r"придур", r"придурок", r"придурки",
    r"урод", r"уроды", r"уродств",
    r"гнид", r"гнида", r"гниды",
    r"падл", r"падла", r"падлы",
    r"дрян", r"дрянь", r"дрянн",
    r"мерзав", r"мерзавец", r"мерзавк",
    r"негодя", r"негодяй",
    r"подлец",
    r"поганец", r"поган",
    r"хам", r"хамл", r"хамск",
    r"наглец", r"нагл",
    r"нахал", r"наха",
    r"хамло",
    r"убью", r"убить", r"зарежу",
    r"прикончу", r"прикончить",
    r"уничтож", r"уничтожу",
    r"порву", r"порвать",
    r"сожгу", r"сжечь",
    r"казн", r"казню", r"казнить",
    r"расправ", r"расправлюсь",
    r"размаж", r"размажу",
    r"раздав", r"раздавлю",
    r"сломаю", r"сломать",
    r"изобью", r"избить",
    r"изнасил", r"изнасилую", r"изнасиловать",
]

BAD_WORDS = [
    "шлюха", "шлюхи", "шлюхой", "шлюху", "шлюшкой", "шлюшка", "шлюшки",
    "шлюшонок", "шлюшонка", "пошлюха",
    "проститутка", "проститутки", "проституткой", "проститутками",
    "путана", "путаны", "путаной",
    "шалава", "шалавы", "шалавой",
    "потаскуха", "потаскухи", "потаскухой",
    "хабалка", "хабалки", "хабалкой",
    "стерва", "стервы", "стервой", "стервозная",
    "курва", "курвы", "курвой",
    "блядь", "бляди", "блядью", "блядство", "блядский",
    "блядина", "блядины", "блядинка",
    "мандавошка", "мандавошки",
    "влагалище", "вагина", "вагины",
    "клитор", "клиторы",
    "сперма", "спермы", "спермой",
    "сволочь", "сволочи", "сволочью", "сволота",
    "мразь", "мрази", "мразью", "мразота",
    "тварь", "твари", "тварью", "тварюга",
    "ублюдок", "ублюдки", "ублюдка",
    "кретин", "кретинка",
    "дебил", "дебилка",
    "идиот", "идиотка",
    "придурок", "придурки", "придурка",
    "урод", "уроды", "уродина", "уродка",
    "гнида", "гниды", "гнидой",
    "падла", "падлы", "падлой", "падлюка",
    "дрянь", "дряни", "дрянью",
    "мерзавец", "мерзавка", "мерзавцы",
    "негодяй", "негодяйка", "негодяи",
    "подлец", "подлюка", "подлецы",
    "поганец", "поганка",
    "хамло", "хамла",
    "наглец", "нахал", "нахалюга",
    "шкура", "шкуры", "шкурой",
    "овца", "овцы",
    "курица", "куриц",
    "сучара", "сучары",
    "шавка", "шавки",
    "лохушка", "лохушки",
    "лох", "лохи", "лохом",
    "чмо", "чмошник", "чмошница",
    "чмырь", "чмыр",
    "быдло", "быдла", "быдлом",
    "кобыла", "кобылы",
    "корова", "коровы",
    "свинья", "свиньи",
    "крыса", "крысы", "крысой",
    "дегенерат", "дегенераты", "дегенератка",
    "олигофрен", "олигофрены", "олигофренка",
    "даун", "дауны", "даунка", "дауненок",
    "аутист", "аутисты", "аутистка",
    "нацист", "нацисты", "нацистка",
    "фашист", "фашисты", "фашистка",
    "гитлер", "гитлера",
    "рашист", "рашисты", "рашизм",
    "хохол", "хохлы", "хохлушка",
    "москаль", "москали",
    "кацап", "кацапы",
    "чурка", "чурки", "чурбан",
    "хач", "хачи", "хачик",
    "жид", "жиды", "жидяра",
    "нигер", "нигеры", "ниггер",
    "черномазый", "черномазая",
    "узкоглазый", "узкоглазая",
]

MAT_PATTERN = re.compile(
    r"(?<![а-яёa-z])(" + "|".join(MAT_ROOTS) + r")[а-яёa-z]*",
    re.IGNORECASE
)

BAD_WORD_PATTERN = re.compile(
    r"(?<![а-яёa-z])(" + "|".join(map(re.escape, BAD_WORDS)) + r")(?![а-яёa-z])",
    re.IGNORECASE
)

# ==================== ТИТУЛЫ ====================

TITLES = [
    "🐉 Повелитель драконов", "🧙 Верховный маг", "👑 Император чата",
    "🤡 Шут гороховый", "🥔 Картофельный магнат", "🐸 Жаба-путешественница",
    "🦆 Утка-ниндзя", "🐱 Кот-философ", "🐶 Пёс-хранитель",
    "🦊 Хитрый лис", "🐻 Медведь-шаман", "🦉 Сова-всезнайка",
    "🐼 Панда-ленивец", "🦁 Лев-царь зверей", "🐧 Пингвин-джентльмен",
    "🦄 Единорог-мечтатель", "🐲 Дракон-хранитель", "👾 Космический захватчик",
    "🤖 Робот-терминатор", "👻 Призрак-невидимка", "🧛 Вампир-полуночник",
    "🧟 Зомби-апокалипсис", "🧜 Русалка-соблазнительница", "🧚 Фея-волшебница",
    "🦸 Супергерой", "🦹 Злодей-мастермайнд", "🥷 Ниндзя-невидимка",
    "🤠 Ковбой Дикого Запада", "👽 Пришелец с Марса", "🎃 Тыква-хэллоуин",
    "🎅 Дед Мороз", "🧝 Эльф-лучник", "🧞 Джинн-исполнитель желаний",
    "🗿 Каменный истукан", "🌮 Тако-гурман", "🍕 Пицца-мастер",
    "🍔 Бургер-король", "🍣 Суши-сенсей", "☕ Кофейный маньяк",
    "🍺 Пивной барон", "🎮 Геймер-легенда", "💻 Кодер-хакер",
    "🎸 Рок-звезда", "🎤 Рэпер-гуф", "🎨 Художник-абстракционист",
    "📚 Книжный червь", "🧠 Мозговой штурм", "💪 Качок-атлет",
    "🏃 Бегун-марафонец", "🛌 Лежебока-профессионал", "🍿 Кинокритик",
    "🎭 Актёр-драмы", "🎪 Клоун-эквилибрист", "🃏 Джокер-шутник",
    "♟️ Шахматный гроссмейстер", "🎯 Снайпер-меткий", "🏆 Чемпион чата",
]

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

# ==================== УТИЛИТЫ ====================

def has_bad_words(text: str) -> bool:
    return bool(MAT_PATTERN.search(text) or BAD_WORD_PATTERN.search(text))


def extract_target_user(message: types.Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        u = message.reply_to_message.from_user
        return u.id, u.full_name

    if message.entities and message.text:
        for entity in message.entities:
            if entity.type == "text_mention" and entity.user:
                u = entity.user
                return u.id, u.full_name
            if entity.type == "mention":
                username = message.text[entity.offset:entity.offset + entity.length]
                return None, username

    return None, None


async def is_admin(message: types.Message) -> bool:
    if message.chat.type == ChatType.PRIVATE:
        return True
    try:
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        return member.status in ("administrator", "creator")
    except Exception as e:
        logging.warning(f"is_admin: {e}")
        return False


async def bot_can_restrict(message: types.Message) -> bool:
    try:
        me = await bot.get_me()
        member = await bot.get_chat_member(message.chat.id, me.id)
        return bool(getattr(member, "can_restrict_members", False))
    except Exception as e:
        logging.warning(f"bot_can_restrict: {e}")
        return False


def parse_minutes(args: list[str]) -> int | None:
    for a in args[1:]:
        if a.isdigit():
            n = int(a)
            if n > 0:
                return n
    return None


# ==================== ОСНОВНЫЕ КОМАНДЫ ====================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я бот-цензор и не только.\n\n"
        "🛡 Удаляю мат автоматически\n"
        "🎲 Имею кучу развлекательных команд\n"
        "🔨 Могу модерировать чат\n\n"
        "📌 Напиши /help для списка команд."
    )


@dp.message(Command("help"))
@dp.message(Command("помощь"))  # русский алиас (в меню не виден, но работает)
async def cmd_help(message: types.Message):
    await message.answer(
        "🛡 <b>Бот-цензор</b>\n\n"
        "<b>🎲 Развлечения:</b>\n"
        "/rps — камень-ножницы-бумага с ботом\n"
        "/rps @user — игра с другим участником (PvP)\n"
        "/dice — бросить кубик (1–6)\n"
        "/coin — орёл или решка\n"
        "/title — выдать смешной титул (себе или reply)\n"
        "/ball &lt;вопрос&gt; — магический шар\n\n"
        "<b>🔨 Модерация (для админов):</b>\n"
        "/kick — кикнуть (reply)\n"
        "/ban — забанить (reply)\n"
        "/tempban &lt;мин&gt; — временный бан (reply)\n"
        "/mute &lt;мин&gt; — замутить (reply)\n"
        "/unmute — снять мут (reply)\n\n"
        "💡 <i>Команды модерации работают через reply на сообщение нарушителя.</i>\n"
        "🇷🇺 <i>Русские алиасы тоже работают: /кнб /кубик /монетка /титул /шар /кик /бан /врембан /мут /размут</i>"
    )


# ==================== РАЗВЛЕКАТЕЛЬНЫЕ ====================

RPS_CHOICES = {
    "rock": "✊ Камень",
    "scissors": "✌️ Ножницы",
    "paper": "✋ Бумага",
}

RPS_BEATS = {
    "rock": "scissors",
    "scissors": "paper",
    "paper": "rock",
}


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


@dp.message(Command("rps"))
@dp.message(Command("кнб"))
async def cmd_rps(message: types.Message):
    args = (message.text or "").split()
    target_id, target_name = extract_target_user(message)

    # Если нет цели — игра с ботом
    if target_id is None and target_name is None:
        # Если в args есть @username, но text_mention не сработал
        bot_choice_key = random.choice(list(RPS_CHOICES.keys()))
        await message.answer(
            f"🤖 Играем с ботом!\n\n"
            f"Мой выбор уже сделан. Нажми свою кнопку:",
            reply_markup=rps_keyboard("bot")
        )
        # Сохраняем выбор бота для игры с ботом
        RPS_GAMES[f"bot:{message.chat.id}:{message.from_user.id}"] = {
            "player_a": message.from_user.id,
            "choice_a": None,
            "choice_b": bot_choice_key,
            "is_bot": True,
            "a_name": message.from_user.full_name,
            "b_name": "🤖 Бот",
        }
        return

    # Если цель — сам автор
    if target_id == message.from_user.id:
        await message.reply("❌ Нельзя играть с самим собой.")
        return

    # Создаём PvP игру
    game_id = f"{message.chat.id}:{message.from_user.id}:{random.randint(1000, 9999)}"
    RPS_GAMES[game_id] = {
        "player_a": message.from_user.id,
        "player_b": target_id,
        "choice_a": None,
        "choice_b": None,
        "is_bot": False,
        "a_name": message.from_user.full_name,
        "b_name": target_name or "Соперник",
    }

    await message.answer(
        f"🎮 <b>Вызов на КНБ!</b>\n\n"
        f"🥊 {message.from_user.mention_html()} vs {target_name or 'Соперник'}\n\n"
        f"Игрок 1, выбери свой ход:",
        reply_markup=rps_keyboard(game_id)
    )


@dp.callback_query(F.data.startswith("rps:"))
async def rps_callback(call: CallbackQuery):
    parts = call.data.split(":")
    if len(parts) != 3:
        await call.answer("Некорректный вызов.")
        return

    _, game_id, choice = parts

    # Игра с ботом
    if game_id == "bot":
        # Ключ: bot:{chat_id}:{user_id}
        key = f"bot:{call.message.chat.id}:{call.from_user.id}"
        game = RPS_GAMES.get(key)
        if not game:
            await call.answer("Игра не найдена. Начни заново: /rps")
            return
        if game["player_a"] != call.from_user.id:
            await call.answer("Эта игра не твоя.", show_alert=True)
            return

        player_choice = choice
        bot_choice = game["choice_b"]
        result = rps_result(player_choice, bot_choice)

        if result == "draw":
            verdict = "🤝 Ничья!"
        elif result == "a":
            verdict = "🎉 Ты победил!"
        else:
            verdict = "😢 Бот победил!"

        await call.message.edit_text(
            f"🎮 <b>КНБ с ботом</b>\n\n"
            f"👤 Ты: {RPS_CHOICES[player_choice]}\n"
            f"🤖 Бот: {RPS_CHOICES[bot_choice]}\n\n"
            f"<b>{verdict}</b>"
        )
        await call.answer()
        RPS_GAMES.pop(key, None)
        return

    # PvP игра
    game = RPS_GAMES.get(game_id)
    if not game:
        await call.answer("Игра не найдена или уже завершена.", show_alert=True)
        return

    user_id = call.from_user.id
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

    # Если оба сделали выбор — показываем результат
    if game["choice_a"] is not None and game["choice_b"] is not None:
        ca = game["choice_a"]
        cb = game["choice_b"]
        result = rps_result(ca, cb)

        if result == "draw":
            verdict = "🤝 Ничья!"
        elif result == "a":
            verdict = f"🏆 Победил {game['a_name']}!"
        else:
            verdict = f"🏆 Победил {game['b_name']}!"

        try:
            await call.message.edit_text(
                f"🎮 <b>КНБ — результат</b>\n\n"
                f"👤 {game['a_name']}: {RPS_CHOICES[ca]}\n"
                f"👤 {game['b_name']}: {RPS_CHOICES[cb]}\n\n"
                f"<b>{verdict}</b>"
            )
        except Exception:
            await call.message.answer(
                f"🎮 <b>КНБ — результат</b>\n\n"
                f"👤 {game['a_name']}: {RPS_CHOICES[ca]}\n"
                f"👤 {game['b_name']}: {RPS_CHOICES[cb]}\n\n"
                f"<b>{verdict}</b>"
            )
        RPS_GAMES.pop(game_id, None)
    else:
        # Один сделал выбор — ждём второго
        await call.message.edit_text(
            f"🎮 <b>КНБ</b>\n\n"
            f"{game['a_name']} vs {game['b_name']}\n\n"
            f"Ожидание второго игрока..."
        )


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


@dp.message(Command("title"))
@dp.message(Command("титул"))
async def cmd_title(message: types.Message):
    user_id, name = extract_target_user(message)

    if name is None:
        name = message.from_user.full_name
        mention = message.from_user.mention_html()
    elif user_id:
        mention = f'<a href="tg://user?id={user_id}">{name}</a>'
    else:
        mention = name

    title = random.choice(TITLES)
    await message.answer(f"👑 {mention} получает титул:\n\n<b>{title}</b>")


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
        await message.reply("❌ Только админы могут использовать эту команду.")
        return
    if not await bot_can_restrict(message):
        await message.reply("❌ У меня нет прав на ограничение участников.")
        return

    user_id, name = extract_target_user(message)
    if user_id is None:
        await message.reply("❌ Ответь (reply) на сообщение пользователя.")
        return

    try:
        await bot.ban_chat_member(message.chat.id, user_id)
        await bot.unban_chat_member(message.chat.id, user_id)
        await message.answer(f"👢 {name} кикнут из чата.")
    except Exception as e:
        await message.reply(f"❌ Не удалось кикнуть: {e}")


@dp.message(Command("ban"))
@dp.message(Command("бан"))
async def cmd_ban(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ Только админы могут использовать эту команду.")
        return
    if not await bot_can_restrict(message):
        await message.reply("❌ У меня нет прав на ограничение участников.")
        return

    user_id, name = extract_target_user(message)
    if user_id is None:
        await message.reply("❌ Ответь (reply) на сообщение пользователя.")
        return

    try:
        await bot.ban_chat_member(message.chat.id, user_id)
        await message.answer(f"🔨 {name} забанен навсегда.")
    except Exception as e:
        await message.reply(f"❌ Не удалось забанить: {e}")


@dp.message(Command("tempban"))
@dp.message(Command("врембан"))
async def cmd_tempban(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ Только админы могут использовать эту команду.")
        return
    if not await bot_can_restrict(message):
        await message.reply("❌ У меня нет прав на ограничение участников.")
        return

    user_id, name = extract_target_user(message)
    if user_id is None:
        await message.reply("❌ Ответь (reply) на сообщение пользователя.")
        return

    args = (message.text or "").split()
    minutes = parse_minutes(args)
    if not minutes:
        await message.reply("❌ Укажи время в минутах: <code>/tempban 30</code>")
        return

    try:
        until_ts = int((datetime.now() + timedelta(minutes=minutes)).timestamp())
        await bot.ban_chat_member(message.chat.id, user_id, until_date=until_ts)
        TEMP_BANS.setdefault(message.chat.id, {})[user_id] = (
            datetime.now() + timedelta(minutes=minutes)
        )
        await message.answer(f"⏱ {name} забанен на <b>{minutes} мин.</b>")
    except Exception as e:
        await message.reply(f"❌ Не удалось забанить: {e}")


@dp.message(Command("mute"))
@dp.message(Command("мут"))
async def cmd_mute(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ Только админы могут использовать эту команду.")
        return
    if not await bot_can_restrict(message):
        await message.reply("❌ У меня нет прав на ограничение участников.")
        return

    user_id, name = extract_target_user(message)
    if user_id is None:
        await message.reply("❌ Ответь (reply) на сообщение пользователя.")
        return

    args = (message.text or "").split()
    minutes = parse_minutes(args)
    if not minutes:
        await message.reply("❌ Укажи время в минутах: <code>/mute 15</code>")
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
        await message.reply(f"❌ Не удалось замутить: {e}")


@dp.message(Command("unmute"))
@dp.message(Command("размут"))
async def cmd_unmute(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ Только админы могут использовать эту команду.")
        return

    user_id, name = extract_target_user(message)
    if user_id is None:
        await message.reply("❌ Ответь (reply) на сообщение пользователя.")
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
        await message.reply(f"❌ Не удалось размутить: {e}")


# ==================== ФИЛЬТР МАТА ====================

@dp.message()
async def filter_messages(message: types.Message):
    if not message.text:
        return
    if message.text.startswith("/"):
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
    """
    ВАЖНО: Telegram показывает в меню только латинские команды
    (a-z, 0-9, _). Русские алиасы работают, но в меню не видны.
    Поэтому здесь только латиница.
    """
    commands = [
        types.BotCommand(command="start", description="Запустить бота"),
        types.BotCommand(command="help", description="Все команды бота"),
        types.BotCommand(command="rps", description="КНБ с ботом или @user"),
        types.BotCommand(command="dice", description="Бросить кубик"),
        types.BotCommand(command="coin", description="Орёл или решка"),
        types.BotCommand(command="title", description="Выдать смешной титул"),
        types.BotCommand(command="ball", description="Магический шар"),
        types.BotCommand(command="kick", description="Кикнуть (reply)"),
        types.BotCommand(command="ban", description="Забанить (reply)"),
        types.BotCommand(command="tempban", description="Врембан в минутах (reply)"),
        types.BotCommand(command="mute", description="Мут в минутах (reply)"),
        types.BotCommand(command="unmute", description="Снять мут (reply)"),
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
