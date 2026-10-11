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
RPS_GAMES = {}
CENSOR_ENABLED = {}
USERNAME_CACHE = {}
# Хранилище статуса автоудаления сервисных сообщений: {chat_id: True/False}
SERVICE_CLEANER_ENABLED = {}

# ==================== НОРМАЛИЗАЦИЯ ====================

HOMOGLYPHS = str.maketrans({
    "a": "а", "A": "а", "e": "е", "E": "е",
    "o": "о", "O": "о", "p": "р", "P": "р",
    "c": "с", "C": "с", "x": "х", "X": "х",
    "y": "у", "Y": "у", "k": "к", "K": "к",
    "m": "м", "M": "м", "t": "т", "T": "т",
    "h": "н", "H": "н", "b": "в", "B": "в",
    "n": "п", "N": "п",
    "0": "о", "1": "и", "3": "з", "4": "а",
    "6": "б", "8": "в", "9": "д",
})

RU_LETTERS_RE = re.compile(r"[^а-яё]")


def normalize_word(word: str) -> str:
    if not word:
        return ""
    word = word.lower()
    word = word.translate(HOMOGLYPHS)
    word = RU_LETTERS_RE.sub("", word)
    word = re.sub(r"(.)\1{2,}", r"\1", word)
    return word


def normalize_flat(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = text.translate(HOMOGLYPHS)
    text = RU_LETTERS_RE.sub("", text)
    text = re.sub(r"(.)\1{2,}", r"\1", text)
    return text


# ==================== СПИСКИ МАТА ====================

MAT_ROOTS_LONG = [
    r"хуйло", r"хуйня", r"хуесос", r"хуисос", r"хуеплёт", r"хуеплет",
    r"хуеглёт", r"хуеглот", r"хуемразь",
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
    r"блядина", r"блядинк", r"блядищ",
    r"блядство", r"блядств", r"блядск", r"блядская",
    r"блядун", r"блядуш",
    r"блядва", r"блядво",
    r"забляд", r"набляд", r"пробляд",
    r"выбляд", r"выблядок",
    r"добляд", r"прибляд",
    r"ебан", r"ёбан", r"ебану", r"ебанут", r"ебанул",
    r"ебат", r"ебать", r"ёбат", r"ёбать", r"ебал", r"ёбал",
    r"ебало", r"ёбало", r"ебальник", r"ебальн",
    r"ебарь", r"ёбарь", r"ебари",
    r"ебуч", r"ёбуч", r"ебучий", r"ёбучий",
    r"ебёт", r"ебет", r"ебётся",
    r"ебить", r"ебитв", r"ебитва",
    r"ебля", r"ёбля", r"ебли", r"ёбли",
    r"ебло", r"ёбло", r"еблом",
    r"еблан", r"ёблан", r"ебланк",
    r"ебств", r"ёбств", r"ебусь", r"ебут",
    r"ебака",
    r"заеб", r"заёб", r"заебал", r"заебись", r"заебу",
    r"заебан", r"заёбан",
    r"наеб", r"наёб", r"наебал", r"наебать", r"наебут",
    r"наебан", r"наёбан", r"наебка",
    r"отъеб", r"отъёб", r"отъебал", r"отъебать",
    r"отъебис", r"отъебись",
    r"подъеб", r"подъёб", r"подъебал", r"подъебка",
    r"подъебну", r"подъёбну",
    r"уебал", r"уебать", r"уебан",
    r"уёбан", r"уебищ", r"уёбищ",
    r"въеб", r"въёб", r"въебал", r"въебать", r"въебну",
    r"проеб", r"проёб", r"проебал", r"проебать",
    r"проебан", r"проёбан", r"проебу",
    r"разъеб", r"разъёб", r"разъебал", r"разъебать",
    r"разъебан", r"разъёбан",
    r"съеб", r"съёб", r"съебал", r"съебать", r"съебался",
    r"съебис", r"съебись",
    r"доебал", r"доебать", r"доебис", r"доебись",
    r"долбоеб", r"долбоёб", r"долбаеб", r"долбаёб",
    r"долбоебк", r"долбоёбк",
    r"недоеб", r"недоёб",
    r"перееб", r"переёб", r"переебал", r"переебать",
    r"переебан", r"переёбан", r"переебу",
    r"поебал", r"поебать",
    r"поебен", r"поебень", r"поебон",
    r"поебушк", r"поебух",
    r"ебалда",
    r"сучка", r"сучки", r"сучонок",
    r"сучара", r"сучарк", r"сучий", r"сучья", r"сучён",
    r"паскуд", r"паскудник",
    r"падлюк", r"падлюка", r"падлючк",
    r"мудак", r"мудачь",
    r"мудил", r"мудила", r"мудило",
    r"мудозвон",
    r"мудень", r"мудня",
    r"замуд", r"намуд", r"промуда",
    r"гандон", r"гондон",
    r"кондом",
    r"пидор", r"пидар", r"пидер",
    r"педик", r"педер", r"педераст",
    r"пидорас", r"пидарас", r"пидорасина",
    r"пидорств", r"пидарств",
    r"пидорок",
    r"гомик", r"гомосек",
    r"залуп", r"залупа", r"залупе", r"залупу",
    r"залупк", r"залупок",
    r"мандавошк", r"мандав", r"мандуй",
    r"шлюха", r"шлюхи", r"шлюхо", r"шлюхе", r"шлюху",
    r"шлюшка", r"шлюшки", r"шлюшк", r"шлюшонк", r"шлюшня",
    r"пошлюх",
    r"проститут", r"проститух",
    r"шалава", r"шалавы", r"шалавищ",
    r"потаскух", r"потаскушк",
    r"хабалка", r"хабалк",
    r"стерва", r"стервы", r"стерво",
    r"блудниц",
    r"влагалищ",
    r"клитор",
    r"спермат", r"сперматозо", r"сперматозоид",
    r"мошонк", r"мошонка",
    r"срака", r"сраку", r"сраки",
    r"срать", r"срала",
    r"срача", r"сраче",
    r"ссать", r"ссала", r"ссанин",
    r"пердёж", r"пердеж", r"пердану",
    r"пердун", r"пердунь",
    r"бздёж", r"бздеж", r"бздун",
    r"какашк",
    r"говно", r"говна", r"говне", r"говну",
    r"говнюк", r"говнюшк",
    r"говня", r"говнян", r"говняст",
    r"дерьм", r"дерьмо", r"дерьма",
    r"мочалк",
    r"фекал", r"фекали",
    r"испражн",
    r"экскремен",
    r"жопа", r"жопу", r"жопе", r"жопы",
    r"жопан", r"жопень",
    r"задниц", r"задница", r"задницу",
    r"анальн",
    r"анусн",
    r"простат", r"простата",
    r"дрочи", r"дрочил", r"дрочить",
    r"дрочер",
    r"онанизм", r"онанист",
    r"мастурб", r"мастурбац", r"мастурби",
    r"минет", r"миньет", r"минетч",
    r"кунилингус", r"кунилинг",
    r"фелляц",
    r"оральн",
    r"сексуаль", r"сексуальн",
    r"половойакт",
    r"совокуп", r"совокуплен",
    r"сношен", r"сношение",
    r"трахат", r"трахаю", r"трахал", r"трахать",
    r"трахнул",
    r"шмара", r"шмары",
    r"подзаборн",
    r"дешевка",
    r"хохол", r"хохлы", r"хохлушк",
    r"москаль", r"москаля",
    r"кацапн",
    r"жидяр",
    r"чурбан",
    r"чучмек",
    r"хачик",
    r"армяшк", r"армяшка",
    r"дагест", r"дагестан",
    r"чечен", r"чеченец",
    r"китаёз", r"китаеза",
    r"немчура",
    r"фашист", r"нацист",
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
    r"наркота", r"наркотик",
    r"наркоман", r"наркоманк",
    r"торчок",
    r"ширнут", r"ширнул",
    r"суицид",
    r"самоубий", r"самоубийств",
    r"повесит", r"повешусь", r"повесил",
    r"убийств", r"убийц",
    r"зарежу",
    r"вскрытвен",
    r"террорист", r"терроризм", r"теракт",
    r"взорвать",
    r"джихад",
    r"шахид",
    r"смертник",
    r"игилов",
    r"алькаид",
    r"талиб",
    r"педофил",
    r"малолетк", r"малолеток",
    r"несовершеннолетн",
    r"сволочь", r"сволочи",
    r"мразь", r"мрази", r"мразот",
    r"тварь", r"твари", r"тварюг",
    r"ублюдок", r"ублюдки",
    r"кретин", r"кретинк",
    r"дебильн",
    r"идиот", r"идиотк",
    r"придурок", r"придурки",
    r"уродств",
    r"гнида", r"гниды",
    r"падлюка",
    r"мерзавец", r"мерзавк",
    r"негодяй",
    r"поганец",
    r"хамло",
    r"нахалюга",
    r"дегенерат",
    r"олигофрен",
    r"дауненок",
    r"аутист",
    r"прикончить",
    r"уничтож",
    r"расправ",
    r"размажу",
    r"раздавлю",
    r"изнасил", r"изнасилую", r"изнасиловать",
    r"хуй", r"хуя", r"хую", r"хуе", r"хуё", r"хуи",
    r"пизд",
    r"бляд", r"блят",
    r"еб", r"ёб",
]

MAT_ROOTS_SHORT = [
    r"хуй", r"хуя", r"хую", r"хуе", r"хуё", r"хуи",
    r"хуел", r"хуею", r"хуев", r"хуёв",
    r"схуя", r"схуй",
    r"хер", r"херов", r"херня", r"хернёй", r"херню", r"херовина",
    r"пизд", r"пизж",
    r"блядь", r"бляди", r"блядо", r"бляде", r"бляду",
    r"блят", r"бляд", r"бля",
    r"еб", r"ёб", r"ебу", r"еби", r"ебуч", r"ёбуч",
    r"сука", r"суки", r"сук", r"сучк",
    r"суч", r"сучар",
    r"засук",
    r"мудор", r"мудень", r"мудня", r"муд",
    r"ганд",
    r"пидр",
    r"гомо",
    r"манда", r"манде", r"манду", r"манды", r"мандо",
    r"шлюх", r"шлюш",
    r"шалав",
    r"потаск",
    r"хабал",
    r"стерв",
    r"курв", r"курва", r"курвы", r"курво",
    r"блуд",
    r"вагин", r"вагина",
    r"сперм", r"сперма",
    r"яичк",
    r"срак",
    r"сру", r"срал",
    r"срач", r"срачь",
    r"ссат", r"ссал", r"ссан", r"ссани",
    r"ссик", r"ссику",
    r"перд", r"пердну",
    r"бзд",
    r"вонюч",
    r"моча", r"мочит", r"мочен",
    r"жоп",
    r"анал",
    r"анус",
    r"дроч",
    r"онан",
    r"фелл",
    r"орал",
    r"секс", r"секса", r"сексу", r"сексе",
    r"полов",
    r"снош",
    r"трах", r"трахн",
    r"шмар",
    r"дешевк",
    r"кацап",
    r"жид",
    r"чурка", r"чурки", r"чурк",
    r"хач", r"хачи",
    r"азерб",
    r"узбек",
    r"немч",
    r"наци",
    r"нарк", r"нарко",
    r"торч",
    r"убит", r"убить",
    r"бомб", r"бомба",
    r"игил",
    r"педо",
    r"мраз",
    r"твар",
    r"урод", r"уроды", r"уродина",
    r"дрян", r"дрянь", r"дрянн",
    r"подлец",
    r"поган",
    r"хам", r"хамл", r"хамск",
    r"наглец", r"нагл",
    r"нахал", r"наха",
    r"убью",
    r"порву", r"порвать",
    r"сожгу", r"сжечь",
    r"казн", r"казню", r"казнить",
    r"размаж",
    r"сломаю", r"сломать",
    r"изобью", r"избить",
]

WHITELIST = {
    "херсон", "херсонес", "херсонский",
    "мандарин", "мандарины", "мандаринка", "мандариновый", "мандаринчик",
    "анализ", "анализа", "аналитик", "аналитика", "анализировать", "аналитический",
    "трахея", "трахеит", "трахеи", "трахеотомия",
    "секстант", "секстанта",
    "сукаленок", "сукаленка",
    "сракозябра", "сракозябры",
    "моченый", "моченая", "моченые", "мочение",
    "оральный", "оральная", "оральное", "оральные",
    "половой", "половая", "половое", "половые", "половинка", "половина",
    "сношение", "сношения",
    "дешевка", "дешевки", "дешевле",
    "соль", "соли", "солью",
    "сиськи", "сиська", "сисек",
    "фаллос", "фаллоса",
    "пенис", "пениса",
    "вагина", "вагины", "вагинальный", "вагинальная",
    "клитор", "клитора", "клиторальный",
    "анальный", "анальная", "анальное",
    "сексуальный", "сексуальная", "сексуальное", "сексуальность",
    "мастурбация",
    "наркотик", "наркотики",
    "хамство", "хамства",
    "поганец",
}

MAT_LONG_PATTERN = re.compile(
    r"(" + "|".join(MAT_ROOTS_LONG) + r")",
    re.IGNORECASE
)

MAT_SHORT_PATTERN = re.compile(
    r"(" + "|".join(MAT_ROOTS_SHORT) + r")",
    re.IGNORECASE
)

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

BAD_WORD_SET = set(w.lower() for w in BAD_WORDS)

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

# ==================== ПРОВЕРКА МАТА ====================

def has_bad_words(text: str) -> bool:
    if not text:
        return False

    raw_tokens = re.findall(r"[A-Za-zА-Яа-яЁё0-9]+", text)

    for raw in raw_tokens:
        token = normalize_word(raw)
        if not token:
            continue
        if token in WHITELIST:
            continue
        if MAT_SHORT_PATTERN.search(token):
            if any(w in token for w in WHITELIST):
                if MAT_LONG_PATTERN.search(token):
                    return True
                continue
            return True
        if token in BAD_WORD_SET:
            return True
        if MAT_LONG_PATTERN.search(token):
            return True

    flat = normalize_flat(text)
    if flat and flat not in WHITELIST:
        if MAT_LONG_PATTERN.search(flat):
            return True

    return False


# ==================== СЕРВИСНЫЕ СООБЩЕНИЯ ====================

# Паттерны сервисных сообщений на разных языках
# (для клиентов, которые присылают их как text, а не как new_chat_members)
SERVICE_PATTERNS = [
    # X пригласил Y / X invited Y
    re.compile(r".+\s+пригласил[а]?\s+.+", re.IGNORECASE),
    re.compile(r".+\s+invited\s+.+", re.IGNORECASE),
    # X добавил Y / X added Y
    re.compile(r".+\s+добавил[а]?\s+.+", re.IGNORECASE),
    re.compile(r".+\s+added\s+.+", re.IGNORECASE),
    # X вступил / X присоединился / X joined
    re.compile(r".+\s+вступил[а]?\s+(в|к)\s+", re.IGNORECASE),
    re.compile(r".+\s+присоединил(ся|ась)\s+", re.IGNORECASE),
    re.compile(r".+\s+joined\s+(the\s+)?group", re.IGNORECASE),
    # X вышел / X покинул / X left
    re.compile(r".+\s+вышел\s+из\s+", re.IGNORECASE),
    re.compile(r".+\s+вышла\s+из\s+", re.IGNORECASE),
    re.compile(r".+\s+покинул[а]?\s+", re.IGNORECASE),
    re.compile(r".+\s+left\s+(the\s+)?group", re.IGNORECASE),
    # X удалил Y / X removed Y
    re.compile(r".+\s+удалил[а]?\s+.+", re.IGNORECASE),
    re.compile(r".+\s+removed\s+.+", re.IGNORECASE),
    # X изменил(а) название группы
    re.compile(r".+\s+изменил[а]?\s+название", re.IGNORECASE),
    # Закреплённое сообщение / Pinned message
    re.compile(r"^(закрепл[её]нн?[оы][ем]?\s+сообщение|pinned\s+message)", re.IGNORECASE),
]


def is_service_message(message: types.Message) -> bool:
    """Проверяет, является ли сообщение сервисным о входе/выходе."""
    # 1) Системные поля Telegram — самый надёжный способ
    if message.new_chat_members:
        return True
    if message.left_chat_member:
        return True
    if getattr(message, "new_chat_title", None):
        return True
    if getattr(message, "new_chat_photo", None):
        return True
    if getattr(message, "delete_chat_photo", None):
        return True
    if getattr(message, "pinned_message", None):
        return True
    if getattr(message, "group_chat_created", None):
        return True
    if getattr(message, "supergroup_chat_created", None):
        return True
    if getattr(message, "channel_chat_created", None):
        return True
    if getattr(message, "migrate_to_chat_id", None):
        return True
    if getattr(message, "migrate_from_chat_id", None):
        return True
    if getattr(message, "video_chat_started", None):
        return True
    if getattr(message, "video_chat_ended", None):
        return True
    if getattr(message, "video_chat_scheduled", None):
        return True
    if getattr(message, "video_chat_participants_invited", None):
        return True
    if getattr(message, "proximity_alert_triggered", None):
        return True
    if getattr(message, "forum_topic_created", None):
        return True
    if getattr(message, "forum_topic_closed", None):
        return True
    if getattr(message, "forum_topic_reopened", None):
        return True

    # 2) Текстовые паттерны — на случай, если Telegram прислал как обычный текст
    # (бывает в некоторых клиентах или при пересылке сервисных сообщений)
    text = message.text or message.caption or ""
    if text:
        # короткие сообщения (<= 200 символов) с упоминанием @username + глагола
        if len(text) <= 200:
            for pattern in SERVICE_PATTERNS:
                if pattern.search(text):
                    # дополнительная проверка: должен быть @username или имя в начале
                    if "@" in text or text[0].isupper():
                        return True

    return False


def service_cleaner_enabled(chat_id: int) -> bool:
    """По умолчанию автоудаление сервисных сообщений включено."""
    return SERVICE_CLEANER_ENABLED.get(chat_id, True)


# ==================== КЭШ ПОЛЬЗОВАТЕЛЕЙ ====================

def cache_user(chat_id: int, user: types.User):
    if not user or not user.username:
        return
    USERNAME_CACHE.setdefault(chat_id, {})[user.username.lower()] = user.id


def resolve_username(chat_id: int, username: str) -> int | None:
    if not username:
        return None
    uname = username.lstrip("@").lower()
    return USERNAME_CACHE.get(chat_id, {}).get(uname)


def extract_username_from_text(text: str) -> str | None:
    if not text:
        return None
    m = re.search(r"@([A-Za-z0-9_]{4,32})", text)
    return m.group(0) if m else None


def extract_user_id_from_text(text: str) -> int | None:
    if not text:
        return None
    m = re.search(r"\b(\d{6,15})\b", text)
    return int(m.group(1)) if m else None


# ==================== ЦЕЛЬ КОМАНДЫ ====================

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


# ==================== ПРОЧИЕ УТИЛИТЫ ====================

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


def parse_minutes(args: list[str]) -> int | None:
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
        await message.reply(
            f"🛡 <b>{name}</b> — админ/владелец чата. "
            f"Его нельзя наказать этой командой."
        )
        return False
    return True


# ==================== КОМАНДЫ ====================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    cache_user(message.chat.id, message.from_user)
    await message.answer(
        "👋 Привет! Я бот-цензор и не только.\n\n"
        "🛡 Удаляю мат автоматически (в т.ч. замаскированный)\n"
        "🧹 Чищу сервисные сообщения (вход/выход/приглашения)\n"
        "🎲 Имею кучу развлекательных команд\n"
        "🔨 Могу модерировать чат\n\n"
        "📌 Напиши /help для списка команд."
    )


@dp.message(Command("help"))
@dp.message(Command("помощь"))
async def cmd_help(message: types.Message):
    await message.answer(
        "🛡 <b>Бот-цензор</b>\n\n"
        "<b>🎲 Развлечения:</b>\n"
        "/rps — КНБ с ботом\n"
        "/rps @user или reply — КНБ с другим участником\n"
        "/dice — бросить кубик (1–6)\n"
        "/coin — орёл или решка\n"
        "/ball &lt;вопрос&gt; — магический шар\n\n"
        "<b>🔨 Модерация (для админов):</b>\n"
        "/delete — удалить сообщение (reply)\n"
        "/kick @user или reply — кикнуть\n"
        "/ban @user или reply — забанить\n"
        "/unban @user или ID — разбанить\n"
        "/tempban &lt;мин&gt; @user или reply — временный бан\n"
        "/mute &lt;мин&gt; @user или reply — замутить\n"
        "/unmute @user или reply — снять мут\n\n"
        "<b>🛡 Управление (для админов):</b>\n"
        "/censor — включить фильтр мата\n"
        "/uncensor — выключить фильтр мата\n"
        "/censor_status — статус фильтра\n"
        "/service_on — включить чистку сервисных сообщений\n"
        "/service_off — выключить чистку\n"
        "/service_status — статус чистки\n\n"
        "🧹 <i>Бот автоматически удаляет:\n"
        "• @X пригласил @Y\n"
        "• @X добавил @Y\n"
        "• @X вступил/присоединился\n"
        "• @X вышел/покинул\n"
        "• @X удалил @Y\n"
        "• закреплённые сообщения</i>"
    )


@dp.message(Command("censor"))
@dp.message(Command("цензура"))
async def cmd_censor_on(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        await message.answer("❌ Команда работает только в группах.")
        return
    if not await is_admin(message):
        await message.reply("❌ Только админы могут управлять цензурой.")
        return
    CENSOR_ENABLED[message.chat.id] = True
    await message.answer("✅ Цензура <b>включена</b>. Мат будет удаляться.")


@dp.message(Command("uncensor"))
@dp.message(Command("безцензуры"))
async def cmd_censor_off(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        await message.answer("❌ Команда работает только в группах.")
        return
    if not await is_admin(message):
        await message.reply("❌ Только админы могут управлять цензурой.")
        return
    CENSOR_ENABLED[message.chat.id] = False
    await message.answer("🔓 Цензура <b>выключена</b>. Мат больше не удаляется.")


@dp.message(Command("censor_status"))
@dp.message(Command("статусцензуры"))
async def cmd_censor_status(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        await message.answer("❌ Команда работает только в группах.")
        return
    status = CENSOR_ENABLED.get(message.chat.id, True)
    emoji = "✅" if status else "🔓"
    state = "включена" if status else "выключена"
    await message.answer(f"{emoji} Цензура сейчас <b>{state}</b>.")


@dp.message(Command("service_on"))
@dp.message(Command("чистка_вкл"))
async def cmd_service_on(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        await message.answer("❌ Команда работает только в группах.")
        return
    if not await is_admin(message):
        await message.reply("❌ Только админы могут управлять чисткой.")
        return
    SERVICE_CLEANER_ENABLED[message.chat.id] = True
    await message.answer("✅ Чистка сервисных сообщений <b>включена</b>.")


@dp.message(Command("service_off"))
@dp.message(Command("чистка_выкл"))
async def cmd_service_off(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        await message.answer("❌ Команда работает только в группах.")
        return
    if not await is_admin(message):
        await message.reply("❌ Только админы могут управлять чисткой.")
        return
    SERVICE_CLEANER_ENABLED[message.chat.id] = False
    await message.answer("🔓 Чистка сервисных сообщений <b>выключена</b>.")


@dp.message(Command("service_status"))
@dp.message(Command("статусчистки"))
async def cmd_service_status(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        await message.answer("❌ Команда работает только в группах.")
        return
    status = SERVICE_CLEANER_ENABLED.get(message.chat.id, True)
    emoji = "✅" if status else "🔓"
    state = "включена" if status else "выключена"
    await message.answer(f"{emoji} Чистка сервисных сообщений <b>{state}</b>.")


# ==================== /delete ====================

@dp.message(Command("delete"))
@dp.message(Command("удалить"))
async def cmd_delete(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        await message.answer("❌ Команда работает только в группах.")
        return
    if not await is_admin(message):
        try:
            await message.delete()
        except Exception:
            pass
        return
    if not await bot_can_delete(message):
        await message.reply("❌ У меня нет прав на удаление сообщений.")
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
        await call.answer("Игра не найдена или уже завершена.", show_alert=True)
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
        await message.reply("❌ Только админы могут использовать эту команду.")
        return
    if not await bot_can_restrict(message):
        await message.reply("❌ У меня нет прав на ограничение участников.")
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
        await message.reply(f"❌ Не удалось забанить: {e}")


@dp.message(Command("unban"))
@dp.message(Command("разбан"))
async def cmd_unban(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ Только админы могут использовать эту команду.")
        return
    if not await bot_can_restrict(message):
        await message.reply("❌ У меня нет прав на ограничение участников.")
        return
    user_id, name, err = await resolve_target(message)
    if err:
        await message.reply(err)
        return
    try:
        await bot.unban_chat_member(message.chat.id, user_id, only_if_banned=True)
        await message.answer(f"🔓 {name} разбанен.")
    except Exception as e:
        await message.reply(f"❌ Не удалось разбанить: {e}")


@dp.message(Command("tempban"))
@dp.message(Command("врембан"))
async def cmd_tempban(message: types.Message):
    if not await is_admin(message):
        await message.reply("❌ Только админы могут использовать эту команду.")
        return
    if not await bot_can_restrict(message):
        await message.reply("❌ У меня нет прав на ограничение участников.")
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
    user_id, name, err = await resolve_target(message)
    if err:
        await message.reply(err)
        return
    if not await check_target(message, user_id, name):
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
        await message.reply(f"❌ Не удалось размутить: {e}")


# ==================== АВТОУДАЛЕНИЕ СЕРВИСНЫХ СООБЩЕНИЙ ====================

@dp.message(F.new_chat_members)
async def on_new_chat_members(message: types.Message):
    """Ловит сервисные сообщения о входе/приглашении."""
    if not service_cleaner_enabled(message.chat.id):
        return
    try:
        await message.delete()
        logging.info(f"Удалено сервисное сообщение (new_chat_members) в {message.chat.id}")
    except Exception as e:
        logging.warning(f"Не удалось удалить сервисное сообщение: {e}")


@dp.message(F.left_chat_member)
async def on_left_chat_member(message: types.Message):
    """Ловит сервисные сообщения о выходе."""
    if not service_cleaner_enabled(message.chat.id):
        return
    try:
        await message.delete()
        logging.info(f"Удалено сервисное сообщение (left_chat_member) в {message.chat.id}")
    except Exception as e:
        logging.warning(f"Не удалось удалить сервисное сообщение: {e}")


@dp.message(F.pinned_message)
async def on_pinned_message(message: types.Message):
    """Ловит сервисные сообщения о закреплении."""
    if not service_cleaner_enabled(message.chat.id):
        return
    try:
        await message.delete()
        logging.info(f"Удалено сервисное сообщение (pinned_message) в {message.chat.id}")
    except Exception as e:
        logging.warning(f"Не удалось удалить сервисное сообщение: {e}")


@dp.message(F.new_chat_title | F.new_chat_photo | F.delete_chat_photo)
async def on_chat_changes(message: types.Message):
    """Ловит сервисные сообщения об изменении названия/аватара чата."""
    if not service_cleaner_enabled(message.chat.id):
        return
    try:
        await message.delete()
        logging.info(f"Удалено сервисное сообщение (chat_changes) в {message.chat.id}")
    except Exception as e:
        logging.warning(f"Не удалось удалить сервисное сообщение: {e}")


@dp.message()
async def filter_messages(message: types.Message):
    """Общий хендлер: кэш + мат + сервисные по тексту."""
    # Кэшируем автора
    if message.from_user:
        cache_user(message.chat.id, message.from_user)
    if message.reply_to_message and message.reply_to_message.from_user:
        cache_user(message.chat.id, message.reply_to_message.from_user)

    # Проверяем сервисные по тексту (для клиентов, которые шлют их как текст)
    if service_cleaner_enabled(message.chat.id) and is_service_message(message):
        try:
            await message.delete()
            logging.info(
                f"Удалено сервисное сообщение (text) в {message.chat.id}"
            )
        except Exception as e:
            logging.warning(f"Не удалось удалить сервисное сообщение: {e}")
        return

    # Мат
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
