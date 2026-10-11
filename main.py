import os
import re
import random
import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode, ChatPermissions
from aiogram.client.default import DefaultBotProperties

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

# Хранилище активных временных банов: {chat_id: {user_id: until_datetime}}
TEMP_BANS = {}
# Хранилище активных мутов: {chat_id: {user_id: until_datetime}}
TEMP_MUTES = {}

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

# ==================== ТИТУЛЫ (для /титул) ====================

TITLES = [
    "🐉 Повелитель драконов",
    "🧙 Верховный маг",
    "👑 Император чата",
    "🤡 Шут гороховый",
    "🥔 Картофельный магнат",
    "🐸 Жаба-путешественница",
    "🦆 Утка-ниндзя",
    "🐱 Кот-философ",
    "🐶 Пёс-хранитель",
    "🦊 Хитрый лис",
    "🐻 Медведь-шаман",
    "🦉 Сова-всезнайка",
    "🐼 Панда-ленивец",
    "🦁 Лев-царь зверей",
    "🐧 Пингвин-джентельмен",
    "🦄 Единорог-мечтатель",
    "🐲 Дракон-хранитель",
    "👾 Космический захватчик",
    "🤖 Робот-терминатор",
    "👻 Призрак-невидимка",
    "🧛 Вампир-полуночник",
    "🧟 Зомби-апокалипсис",
    "🧜 Русалка-соблазнительница",
    "🧚 Фея-волшебница",
    "🦸 Супергерой",
    "🦹 Злодей-мастермайнд",
    "🥷 Ниндзя-невидимка",
    "🤠 Ковбой Дикого Запада",
    "👽 Пришелец с Марса",
    "🎃 Тыква-хэллоуин",
    "🎅 Дед Мороз",
    "🧝 Эльф-лучник",
    "🧞 Джинн-исполнитель желаний",
    "🗿 Каменный истукан",
    "🌮 Тако-гурман",
    "🍕 Пицца-мастер",
    "🍔 Бургер-король",
    "🍣 Суши-сенсей",
    "☕ Кофейный маньяк",
    "🍺 Пивной барон",
    "🎮 Геймер-легенда",
    "💻 Кодер-хакер",
    "🎸 Рок-звезда",
    "🎤 Рэпер-гуф",
    "🎨 Художник-абстракционист",
    "📚 Книжный червь",
    "🧠 Мозговой штурм",
    "💪 Качок-атлет",
    "🏃 Бегун-марафонец",
    "🛌 Лежебока-профессионал",
    "🍿 Кинокритик",
    "🎭 Актёр-драмы",
    "🎪 Клоун-эквилибрист",
    "🃏 Джокер-шутник",
    "♟️ Шахматный гроссмейстер",
    "🎯 Снайпер-меткий",
    "🏆 Чемпион чата",
]

# ==================== МАГИЧЕСКИЙ ШАР ====================

MAGIC_8_BALL = [
    "🎱 Да, однозначно.",
    "🎱 Нет, даже не думай.",
    "🎱 Возможно.",
    "🎱 Спроси позже.",
    "🎱 Не могу сказать сейчас.",
    "🎱 Абсолютно точно.",
    "🎱 Скорее нет, чем да.",
    "🎱 Скорее да, чем нет.",
    "🎱 Не рассчитывай на это.",
    "🎱 Все звёзды за.",
    "🎱 Мои источники говорят «нет».",
    "🎱 Определённо да.",
    "🎱 Сомневаюсь.",
    "🎱 Знаки говорят «да».",
    "🎱 Туманно, попробуй ещё раз.",
    "🎱 Да, но осторожно.",
    "🎱 Лучше не спрашивай.",
    "🎱 Всё возможно в этом мире.",
    "🎱 Судьба решит за тебя.",
    "🎱 Я бы на твоём месте подумал.",
]

# ==================== УТИЛИТЫ ====================

def has_bad_words(text: str) -> bool:
    return bool(MAT_PATTERN.search(text) or BAD_WORD_PATTERN.search(text))


def extract_target_user(message: types.Message):
    """
    Возвращает (user_id, display_name) цели:
    - из reply, если это ответ на сообщение
    - из @mention или text_mention в тексте
    """
    # 1) Если это ответ на сообщение
    if message.reply_to_message and message.reply_to_message.from_user:
        u = message.reply_to_message.from_user
        return u.id, u.full_name

    # 2) Если в тексте есть @username или text_mention
    if message.entities:
        for entity in message.entities:
            if entity.type == "text_mention" and entity.user:
                return entity.user.id, entity.user.full_name
            if entity.type == "mention":
                # @username — ID не узнаем без резолва, вернём username
                username = message.text[entity.offset:entity.offset + entity.length]
                return None, username

    return None, None


async def is_admin(message: types.Message) -> bool:
    """Проверяет, является ли автор админом в чате."""
    if message.chat.type == "private":
        return True
    try:
        member = await message.chat.get_member(message.from_user.id)
        return member.status in ("administrator", "creator")
    except Exception:
        return False


async def bot_can_restrict(message: types.Message) -> bool:
    """Проверяет, может ли бот ограничивать участников."""
    try:
        me = await message.chat.get_member((await bot.get_me()).id)
        return getattr(me, "can_restrict_members", False)
    except Exception:
        return False


# ==================== ОСНОВНЫЕ КОМАНДЫ ====================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я бот-цензор и не только.\n\n"
        "🛡 Удаляю мат автоматически\n"
        "🎲 Имею кучу развлекательных команд\n"
        "🔨 Могу модерировать чат\n\n"
        "📌 Напиши /помощь для списка команд."
    )


@dp.message(Command("помощь", "help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "🛡 <b>Бот-цензор</b>\n\n"
        "<b>🎲 Развлечения:</b>\n"
        "/кнб — камень-ножницы-бумага\n"
        "/кубик — бросить кубик (1–6)\n"
        "/монетка — орёл или решка\n"
        "/титул @user — выдать смешной титул\n"
        "/шар &lt;вопрос&gt; — магический шар\n\n"
        "<b>🔨 Модерация (для админов):</b>\n"
        "/кик @user — кикнуть участника\n"
        "/бан @user — забанить\n"
        "/врембан @user &lt;мин&gt; — временный бан\n"
        "/мут @user &lt;мин&gt; — замутить\n"
        "/размут @user — снять мут\n\n"
        "💡 <i>Вместо @user можно ответить (reply) на сообщение.</i>"
    )


# ==================== РАЗВЛЕКАТЕЛЬНЫЕ КОМАНДЫ ====================

@dp.message(Command("кнб"))
async def cmd_rps(message: types.Message):
    choices = ["✊ Камень", "✌️ Ножницы", "✋ Бумага"]
    bot_choice = random.choice(choices)
    await message.answer(
        f"🤖 Мой выбор: <b>{bot_choice}</b>\n\n"
        f"А ты что выберешь? Напиши: камень / ножницы / бумага"
    )


@dp.message(Command("кубик"))
async def cmd_dice(message: types.Message):
    value = random.randint(1, 6)
    await message.answer(f"🎲 Выпало: <b>{value}</b>")


@dp.message(Command("монетка"))
async def cmd_coin(message: types.Message):
    result = random.choice(["🪙 Орёл", "🪙 Решка"])
    await message.answer(f"Подбрасываю... <b>{result}</b>")


@dp.message(Command("титул"))
async def cmd_title(message: types.Message):
    user_id, name = extract_target_user(message)

    if name is None:
        # Нет цели — выдаём титул самому автору
        name = message.from_user.full_name
        mention = message.from_user.mention_html()
    else:
        mention = f'<a href="tg://user?id={user_id}">{name}</a>' if user_id else name

    title = random.choice(TITLES)
    await message.answer(f"👑 {mention} получает титул:\n\n<b>{title}</b>")


@dp.message(Command("шар"))
async def cmd_ball(message: types.Message):
    # Отрезаем команду от текста
    text = message.text or ""
    parts = text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer("🔮 Задай вопрос: <code>/шар Я стану миллионером?</code>")
        return

    question = parts[1].strip()
    answer = random.choice(MAGIC_8_BALL)
    await message.answer(f"❓ <i>{question}</i>\n\n{answer}")


# ==================== МОДЕРАЦИЯ ====================

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
        await message.reply(
            "❌ Укажи пользователя через reply или @username "
            "(у @username нужен user_id — лучше отвечай reply)."
        )
        return

    try:
        await message.chat.ban(user_id)
        await message.chat.unban(user_id)  # сразу разбаниваем = кик
        await message.answer(f"👢 {name} кикнут из чата.")
    except Exception as e:
        await message.reply(f"❌ Не удалось кикнуть: {e}")


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
        await message.reply(
            "❌ Укажи пользователя через reply или @username."
        )
        return

    try:
        await message.chat.ban(user_id)
        await message.answer(f"🔨 {name} забанен навсегда.")
    except Exception as e:
        await message.reply(f"❌ Не удалось забанить: {e}")


@dp.message(Command("врембан"))
async def cmd_tempban(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ Только админы могут использовать эту команду.")
        return
    if not await bot_can_restrict(message):
        await message.reply("❌ У меня нет прав на ограничение участников.")
        return

    # Парсим: /врембан <цель> <минуты>
    # Цель может быть из reply, а минуты — второй аргумент
    args = (message.text or "").split()
    minutes = None

    # Если reply — минуты во втором слове
    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
        name = message.reply_to_message.from_user.full_name
        if len(args) >= 2 and args[1].isdigit():
            minutes = int(args[1])
    else:
        # Без reply: /врембан @user 30
        user_id, name = extract_target_user(message)
        if len(args) >= 3 and args[-1].isdigit():
            minutes = int(args[-1])

    if user_id is None:
        await message.reply("❌ Укажи пользователя (reply) и время в минутах.")
        return
    if not minutes or minutes <= 0:
        await message.reply("❌ Укажи время в минутах, например: <code>/врембан 30</code>")
        return

    try:
        await message.chat.ban(user_id)
        until = datetime.now() + timedelta(minutes=minutes)
        TEMP_BANS.setdefault(message.chat.id, {})[user_id] = until
        await message.answer(f"⏱ {name} забанен на <b>{minutes} мин.</b>")

        # Планируем разбан
        asyncio.create_task(_auto_unban(message.chat.id, user_id, minutes))
    except Exception as e:
        await message.reply(f"❌ Не удалось забанить: {e}")


async def _auto_unban(chat_id: int, user_id: int, minutes: int):
    await asyncio.sleep(minutes * 60)
    try:
        await bot.unban_chat_member(chat_id, user_id, only_if_banned=True)
        TEMP_BANS.get(chat_id, {}).pop(user_id, None)
        await bot.send_message(chat_id, f"✅ Временный бан истёк, пользователь разбанен.")
    except Exception as e:
        logging.warning(f"Не удалось разбанить: {e}")


@dp.message(Command("мут"))
async def cmd_mute(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ Только админы могут использовать эту команду.")
        return
    if not await bot_can_restrict(message):
        await message.reply("❌ У меня нет прав на ограничение участников.")
        return

    args = (message.text or "").split()
    minutes = None

    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
        name = message.reply_to_message.from_user.full_name
        if len(args) >= 2 and args[1].isdigit():
            minutes = int(args[1])
    else:
        user_id, name = extract_target_user(message)
        if len(args) >= 3 and args[-1].isdigit():
            minutes = int(args[-1])

    if user_id is None:
        await message.reply("❌ Укажи пользователя (reply) и время в минутах.")
        return
    if not minutes or minutes <= 0:
        await message.reply("❌ Укажи время в минутах, например: <code>/мут 15</code>")
        return

    try:
        until = datetime.now() + timedelta(minutes=minutes)
        await message.chat.restrict(
            user_id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until
        )
        TEMP_MUTES.setdefault(message.chat.id, {})[user_id] = until
        await message.answer(f"🔇 {name} замучен на <b>{minutes} мин.</b>")
    except Exception as e:
        await message.reply(f"❌ Не удалось замутить: {e}")


@dp.message(Command("размут"))
async def cmd_unmute(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ Только админы могут использовать эту команду.")
        return

    user_id, name = extract_target_user(message)
    if user_id is None:
        await message.reply("❌ Укажи пользователя через reply.")
        return

    try:
        await message.chat.restrict(
            user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_send_polls=True,
            )
        )
        TEMP_MUTES.get(message.chat.id, {}).pop(user_id, None)
        await message.answer(f"🔊 {name} размучен.")
    except Exception as e:
        await message.reply(f"❌ Не удалось размутить: {e}")


# ==================== ФИЛЬТР МАТА (должен быть ПОСЛЕДНИМ) ====================

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
    commands = [
        types.BotCommand(command="start", description="Запустить бота"),
        types.BotCommand(command="помощь", description="Список всех команд"),
        types.BotCommand(command="кнб", description="Камень-ножницы-бумага"),
        types.BotCommand(command="кубик", description="Бросить кубик"),
        types.BotCommand(command="монетка", description="Орёл или решка"),
        types.BotCommand(command="титул", description="Выдать смешной титул"),
        types.BotCommand(command="шар", description="Магический шар"),
        types.BotCommand(command="кик", description="Кикнуть участника"),
        types.BotCommand(command="бан", description="Забанить участника"),
        types.BotCommand(command="врембан", description="Временный бан"),
        types.BotCommand(command="мут", description="Замутить участника"),
        types.BotCommand(command="размут", description="Размутить участника"),
    ]
    await bot.set_my_commands(commands)


# ==================== ЗАПУСК ====================

async def main():
    await set_commands()
    logging.info("Бот-цензор запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
