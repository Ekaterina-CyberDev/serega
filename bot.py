# bot.py - ИСПРАВЛЕННАЯ ВЕРСИЯ (работают кнопки)

import asyncio
import random
import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import Command
from aiogram.client.session.aiohttp import AiohttpSession
import logging

# ==================== НАСТРОЙКИ ====================
PROXY_URL = "socks5://127.0.0.1:10808"

TOKEN = "8888650931:AAEbMJk7V298o-PwpG4g7LKBWUt-jGMG-t8"
BOT_USERNAME = "@my_happy_birsday_bot"

BIRTHDAY = datetime(2026, 8, 15)
USER_ID = 864762736
SURPRISE_URL = "https://your-website.com/birthday"

# ID ВАШЕЙ ГРУППЫ (укажите правильный!)
GROUP_ID = -1003850535265

# Папки для хранения
MEDIA_FOLDER = "memories_media"
os.makedirs(MEDIA_FOLDER, exist_ok=True)
os.makedirs(f"{MEDIA_FOLDER}/voices", exist_ok=True)
os.makedirs(f"{MEDIA_FOLDER}/video_notes", exist_ok=True)
os.makedirs(f"{MEDIA_FOLDER}/photos", exist_ok=True)
os.makedirs(f"{MEDIA_FOLDER}/videos", exist_ok=True)

MEMORIES_FILE = "memories.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== ЗАГРУЗКА/СОХРАНЕНИЕ МОМЕНТОВ ====================

def load_memories() -> List[Dict[str, Any]]:
    """Загружает памятные моменты из файла"""
    if os.path.exists(MEMORIES_FILE):
        try:
            with open(MEMORIES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                return []
        except Exception as e:
            logger.error(f"Ошибка загрузки: {e}")
            return []
    return []

def save_memories(memories: List[Dict[str, Any]]):
    """Сохраняет памятные моменты в файл"""
    try:
        with open(MEMORIES_FILE, 'w', encoding='utf-8') as f:
            json.dump(memories, f, ensure_ascii=False, indent=2, default=str)
        logger.info(f"Сохранено {len(memories)} моментов")
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")

# Загружаем существующие моменты
MEMORIES = load_memories()
logger.info(f"Загружено {len(MEMORIES)} памятных моментов")

# ==================== РАСШИРЕННАЯ ГЕНЕРАЦИЯ ====================

# Счётчик для уникальности (чтобы комплименты не повторялись)
_generated_cache = set()
_last_date = None

def _get_daily_seed() -> str:
    """Возвращает уникальную соль на основе даты"""
    global _last_date
    today = datetime.now().strftime("%Y-%m-%d")
    if _last_date != today:
        _generated_cache.clear()
        _last_date = today
    return today

# 1. ЗАГОТОВКИ ДЛЯ ГЕНЕРАЦИИ (сильно расширены!)
COMPLIMENT_PARTS = {
    "intro": [
        "Ты", "Каждый день с тобой", "Твоя улыбка", "Твои глаза", 
        "Твоя доброта", "Твой смех", "Твоё сердце", "Твоя душа",
        "Твоя забота", "Твоя нежность", "Твоя поддержка", "Твоя искренность",
        "Твоя сила", "Твоя мудрость", "Твоя уверенность", "Твой взгляд",
        "Твой голос", "Твоя стойкость", "Твоя щедрость", "Твоя открытость",
        "То, как ты улыбаешься", "То, как ты смотришь на меня", "То, как ты обнимаешь",
        "Твой шёпот ночью", "Твои дурацкие шутки", "Твоя привычка гладить меня по голове"
    ],
    "action": [
        "освещает", "делает", "превращает", "наполняет", 
        "дарит", "создаёт", "приносит", "заставляет",
        "спасает", "исцеляет", "вдохновляет", "заряжает",
        "успокаивает", "согревает", "окрыляет", "оберегает",
        "меняет", "украшает", "защищает", "поддерживает"
    ],
    "object": [
        "мой день", "мою жизнь", "этот мир", "каждое утро",
        "все вокруг", "серые будни", "простые моменты", "даже дождь",
        "моё настроение", "мои мысли", "моё сердце", "мою душу",
        "даже самую тяжёлую минуту", "мои страхи", "пустоту внутри",
        "каждый час без тебя", "даже разлуку"
    ],
    "quality": [
        "волшебным ✨", "ярким 🌟", "прекрасным 💫", "незабываемым 💝",
        "особенным 🎀", "тёплым ☀️", "счастливым 🦋", "удивительным 🌈",
        "лучезарным ☀️", "светлым 💛", "бесконечным ♾️", "родным 🏠",
        "неповторимым 💎", "искренним 💕", "настоящим 🎯", "чистым 💧",
        "глубоким 🌊", "магическим ✨", "легендарным 🔥", "абсолютным 💯"
    ]
}

# 2. ЦЕЛЫЕ ИСКРЕННИЕ КОМПЛИМЕНТЫ (как реальные сообщения от девушки)
HEARTFELT_COMPLIMENTS = [
    "Я смотрю на тебя и каждый раз заново влюбляюсь. Ты — моё чудо, которое я даже не мечтала встретить. ❤️",
    "Знаешь, в этом безумном мире ты — мой самый надёжный берег. Спасибо, что ты есть. 💕",
    "Ты даже не представляешь, как сильно я тебя люблю. Иногда просто смотрю на тебя и думаю: 'Боже, какой же он у меня классный'. 💫",
    "Когда ты рядом, все проблемы кажутся такими маленькими. Ты — моя сила и моя защита. 🛡️",
    "Твоя улыбка способна растопить даже самое холодное сердце. А я растаяла уже давно. 🌸",
    "Я люблю не какого-то идеального принца. Я люблю именно тебя — со всеми твоими тараканами, привычками и тем, как ты смешно храпишь. 🦗",
    "Спасибо, что терпишь меня в мои плохие дни. Ты — настоящий герой. 🦸‍♂️",
    "Твои объятия лечат лучше любых таблеток. Очень жду момента, когда смогу снова в них утонуть. 🤗",
    "Ты — моя радость, которую я даже не заслужила, но очень берегу. Ты лучший, помни это. 💖",
    "Иногда ловлю себя на мысли, что ты — моя самая большая удача. И я никому тебя не отдам. 😤",
    "Ты очень умный. Не просто 'умный', а по-настоящему глубокий, интересный человек. Мне никогда не скучно с тобой. 🧠",
    "Я горжусь тобой. Каждый день. Даже когда ты просто встаёшь с дивана, чтобы сделать мне чай. ☕",
    "Твоя доброта делает этот мир лучше. Ты даже не замечаешь, как много хорошего ты делаешь для окружающих. 🌍",
    "Люблю смотреть, как ты увлечён делом. У тебя такой сосредоточенный взгляд — я просто таю. 🔥",
    "Спасибо, что ты есть. Просто за то, что ты живёшь на этой планете в одно время со мной. 🌏"
]

# 3. МОТИВАЦИОННЫЕ СООБЩЕНИЯ (новое!)
MOTIVATIONAL_MESSAGES = [
    "Ты у меня самый лучший, помни это. Никогда не сомневайся в себе. 💪",
    "Ты очень умный и талантливый. У тебя всё получится, даже если сейчас кажется, что нет. 🧠",
    "Ты большой молодец! Я так горжусь тем, какой ты есть. Продолжай в том же духе. 🌟",
    "Никогда не сдавайся. Ты сильнее, чем думаешь. А если устанешь — я рядом, подстрахую. 🛡️",
    "Ты справишься с любой задачей. Ты доказывал это уже много раз. Верю в тебя. 🔥",
    "Даже если сегодня трудный день — помни, что дома тебя любят и ждут. Ты не один. 🏠",
    "Ты — моя опора, но и я хочу быть твоим тылом. Отдыхай, когда нужно. Ты заслуживаешь покоя. 😴",
    "Твоя целеустремлённость восхищает меня. Рядом с тобой я сама становлюсь лучше. 💫",
    "Ты умеешь находить выход даже из самых сложных ситуаций. Это настоящий талант. 🧩",
    "Просто сегодня: ты молодец. Я тебя очень люблю и верю в тебя бесконечно. 💯"
]

# 4. СЛОВАРЬ СИНОНИМОВ (расширен)
SYNONYMS = {
    "красивый": ["прекрасный", "великолепный", "восхитительный", "очаровательный", "изумительный", "божественный", "шикарный", "потрясающий"],
    "умный": ["гениальный", "мудрый", "проницательный", "талантливый", "блистательный", "эрудированный", "смышлёный", "сообразительный"],
    "добрый": ["душевный", "чуткий", "отзывчивый", "нежный", "заботливый", "сердечный", "мягкий", "ласковый"],
    "люблю": ["обожаю", "боготворю", "обожествляю", "ценю", "дороже всех", "балдею от тебя", "тащусь от тебя", "без ума от тебя"],
    "сильный": ["мощный", "несгибаемый", "стойкий", "мужественный", "крепкий", "надёжный", "железный"],
    "весёлый": ["жизнерадостный", "юморной", "забавный", "смешной", "остроумный", "искромётный"]
}

# 5. ТЕМАТИЧЕСКИЕ ПРИВЯЗКИ (расширены)
TIME_THEMES = {
    "morning": {
        "emoji": "🌅",
        "themes": ["новый день", "рассвет", "утренние лучи", "пробуждение", "кофе с тобой", "утренний поцелуй"],
        "compliments": [
            "Пусть сегодняшний день будет таким же прекрасным, как твоя улыбка ☀️",
            "Ты — лучшее, что может случиться в новом дне. Доброе утро, мой хороший 💕",
            "С тобой даже утро становится волшебным. Спасибо, что ты проснулся в моей жизни 🌸",
            "Твоя энергия с утра заряжает меня на целый день. Ты мой маленький ураганчик 🌪️",
            "Надеюсь, ты выспался. Ты мне нужен отдохнувшим и счастливым, понял? 😘"
        ]
    },
    "afternoon": {
        "emoji": "☀️",
        "themes": ["солнце в зените", "яркий полдень", "тёплый день", "обеденный перерыв", "середина дня"],
        "compliments": [
            "Ты освещаешь мой день ярче солнца. Даже если на улице пасмурно 🌤️",
            "Даже в самый загруженный день ты — лучик света, который пробивается сквозь тучи 🌈",
            "Твоя энергия заряжает меня на весь день. Спасибо, что ты такой классный ⚡",
            "Как твой день проходит? Надеюсь, ты успеваешь отдыхать. Ты заслуживаешь самого лучшего 💖",
            "Я тут думала о тебе (как обычно) и поняла — ты реально делаешь мою жизнь ярче. Даже в обычный вторник ✨"
        ]
    },
    "evening": {
        "emoji": "🌤️",
        "themes": ["закат", "вечерние огни", "уютный вечер", "время ужина", "после работы"],
        "compliments": [
            "Твой голос звучит как любимая мелодия вечером. Могу слушать бесконечно 🎵",
            "Ты — самый тёплый лучик заходящего солнца. Укутай меня в свою нежность 🌙",
            "Вечер становится волшебным, когда я знаю, что ты где-то там, думаешь обо мне 💫",
            "Как прошёл твой день? Расскажешь? Я очень хочу знать всё, что с тобой происходит 🫂",
            "Ты даже не представляешь, как я жду момента, когда мы снова будем рядом. Скучаю. Очень. 💕"
        ]
    },
    "night": {
        "emoji": "🌙",
        "themes": ["звёздное небо", "ночная тишина", "лунный свет", "время спать", "полночь"],
        "compliments": [
            "Ты сияешь ярче всех звёзд на небе. И даже Луна завидует 🌟",
            "Спокойной ночи, моя луна и звёзды. Пусть тебе приснится что-то очень тёплое 🌙",
            "Ты — моя путеводная звезда в ночи. Даже в темноте я знаю, куда идти ✨",
            "Перед сном я всегда думаю о тебе. Ты моя самая приятная мысль на ночь 😴",
            "Засыпай спокойно. Я буду охранять твой сон (даже если я далеко). Ты в безопасности. 🛡️"
        ]
    }
}

# 6. ЛИЧНЫЕ ОБРАЩЕНИЯ (расширены, более ласковые)
PERSONAL_NICKNAMES = [
    "мой любимый человек", "моё солнышко", "моя радость", "моё счастье",
    "самый родной", "моя вселенная", "мой самый близкий", "смысл моей жизни",
    "мой хороший", "мой котик", "мой герой", "мой мужчина", "мой сладкий",
    "мой родной", "мой лучший", "мой единственный", "мой космос", "мой воздух"
]

# 7. ЭМОЦИОНАЛЬНЫЕ УКРАШЕНИЯ (расширены)
EMOTIONAL_DECORATIONS = [
    "💕", "💖", "💗", "💓", "💝", "💞", "💟", "❣️", "❤️", "🧡", "💛", "💚", "💙", "💜",
    "✨", "🌟", "⭐", "💫", "⚡", "🌸", "🌺", "🌻", "🌼", "🌷", "🌹",
    "🎀", "🎈", "🎉", "🎊", "💐", "🍀", "🦋", "🌈", "☀️", "🌙", "⭐", "🔥", "💎"
]

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def get_time_of_day() -> str:
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 22:
        return "evening"
    else:
        return "night"

def get_unique_compliment() -> str:
    """Генерирует уникальный комплимент (не повторяется в течение дня)"""
    global _generated_cache
    
    # Создаём 5 разных вариантов и выбираем уникальный
    for _ in range(20):  # максимум 20 попыток
        # Случайно выбираем тип комплимента
        compliment_type = random.choice(["combo", "heartfelt", "themed", "love_quote", "nature", "personal"])
        
        if compliment_type == "combo":
            intro = random.choice(COMPLIMENT_PARTS["intro"])
            action = random.choice(COMPLIMENT_PARTS["action"])
            obj = random.choice(COMPLIMENT_PARTS["object"])
            quality = random.choice(COMPLIMENT_PARTS["quality"])
            nickname = random.choice(PERSONAL_NICKNAMES) if random.random() > 0.5 else None
            
            if nickname:
                compliment = f"{intro}, {nickname}, {action} {obj} {quality}. {random.choice(HEARTFELT_COMPLIMENTS)[:50]}"
            else:
                compliment = f"{intro} {action} {obj} {quality}. {random.choice(HEARTFELT_COMPLIMENTS)[:40]}"
        
        elif compliment_type == "heartfelt":
            compliment = random.choice(HEARTFELT_COMPLIMENTS)
        
        elif compliment_type == "themed":
            time_of_day = get_time_of_day()
            theme = TIME_THEMES[time_of_day]
            compliment = random.choice(theme["compliments"])
        
        elif compliment_type == "love_quote":
            quote_templates = [
                "Я искала тебя во всех людях, но нашла только в тебе. Ты — мой единственный. 💕",
                "С тобой я поняла, что значит 'жить полной жизнью'. Спасибо за каждый день. 💫",
                "Каждый день я открываю в тебе что-то новое и влюбляюсь заново. И это бесконечный процесс ✨",
                "Ты — мой самый любимый сон, который стал реальностью. Никогда не просыпайся рядом со мной 🌙",
                "Я люблю тебя не за что-то, а вопреки всему. И это самое сильное чувство в моей жизни. ❤️",
                "Ты — единственный человек, с которым я хочу стареть. Давай состаримся вместе? 👵👴",
                "С тобой даже проблемы решаются легче, потому что ты — моя сила. А я — твоя поддержка. 💪",
                "Твоя любовь — это самый ценный подарок, который я когда-либо получала. И я буду беречь его вечно. 🎁"
            ]
            compliment = random.choice(quote_templates)
        
        elif compliment_type == "nature":
            nature_templates = [
                f"Ты как {random.choice(['весенний цветок', 'летний ветер', 'осенний лист', 'зимняя звезда'])} — прекрасен и уникален. Никого нет похожего на тебя. 🌸",
                f"Твоя душа — как {random.choice(['океан глубиной в вечность', 'бескрайнее небо', 'чистое утро'])}. Я могу смотреть в тебя бесконечно. 💫",
                f"Твоя доброта сравнится разве что с {random.choice(['солнечным светом', 'тёплым дождём', 'первым снегом'])}. Ты согреваешь всех вокруг. ☀️"
            ]
            compliment = random.choice(nature_templates)
        
        else:  # personal
            templates = [
                f"{random.choice(PERSONAL_NICKNAMES)}, ты — {random.choice(['неповторимый', 'единственный', 'самый лучший', 'мой мир', 'всё для меня'])}! Спасибо, что ты есть. 💕",
                f"С тобой, {random.choice(PERSONAL_NICKNAMES)}, даже {random.choice(['хмурый день', 'трудная задача', 'обычный момент'])} становится праздником. Ты умеешь делать жизнь ярче. 🎉",
                f"Знаешь, {random.choice(PERSONAL_NICKNAMES)}, я {random.choice(['безумно', 'невероятно', 'до безумия', 'так сильно', 'бесконечно'])} тебя {random.choice(SYNONYMS['люблю'])}! И буду любить всегда. 💖"
            ]
            compliment = random.choice(templates)
        
        # Проверяем на уникальность (хеш от комплимента + соль дня)
        compliment_hash = hashlib.md5(compliment.encode()).hexdigest()
        if compliment_hash not in _generated_cache:
            _generated_cache.add(compliment_hash)
            # Добавляем случайную эмодзи-украшалку в конец
            if random.random() > 0.7:
                compliment += f" {random.choice(EMOTIONAL_DECORATIONS)}"
            return compliment
    
    # Если не удалось найти уникальный (почти невозможно), возвращаем heartfelt
    return random.choice(HEARTFELT_COMPLIMENTS)

def get_motivation() -> str:
    """Возвращает мотивационное сообщение"""
    return random.choice(MOTIVATIONAL_MESSAGES)

def get_daily_message_with_ai() -> str:
    """Генерирует ежедневное сообщение с комплиментом + мотивацией"""
    days = get_days_left()
    
    if days == 0:
        return f"🎉🎂 СЕГОДНЯ ТВОЙ ДЕНЬ! 🎂🎉\n\nСсылка на сюрприз:\n{SURPRISE_URL}\n\nС Днём Рождения, любимый! ❤️\n\n{get_unique_compliment()}"
    
    compliment = get_unique_compliment()
    motivation = get_motivation() if random.random() > 0.6 else ""
    
    templates = [
        f"🌅 Доброе утро! До твоего ДР осталось {days} дней!\n\n{compliment}",
        f"💫 С каждым днём ты становишься ещё прекраснее! До ДР: {days} дней.\n\n{compliment}",
        f"⭐ Сегодня {days} {'день' if days == 1 else 'дней'} до твоего праздника!\n\n{compliment}",
        f"🌸 Ещё {days} {'день' if days == 1 else 'дней'} - и будет ПРАЗДНИК!\n\n{compliment}",
        f"🎈 Всего {days} {'день' if days == 1 else 'дней'} до твоего Дня Рождения!\n\n{compliment}",
        f"✨ Сегодня особенный отчёт: {days} {'день' if days == 1 else 'дней'} до твоего ДР ✨\n\n{compliment}",
        f"💝 Мой счётчик любви показывает: {days} {'день' if days == 1 else 'дней'} до твоего праздника!\n\n{compliment}",
        f"🎀 {days} {'день' if days == 1 else 'дней'} отделяют нас от твоего Дня Рождения!\n\n{compliment}"
    ]
    
    message = random.choice(templates)
    if motivation:
        message += f"\n\n💪 {motivation}"
    
    return message

def get_days_left() -> int:
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    birthday_this_year = BIRTHDAY.replace(year=today.year)
    if birthday_this_year < today:
        birthday_this_year = birthday_this_year.replace(year=today.year + 1)
    return (birthday_this_year - today).days

def generate_memory_id() -> str:
    """Генерирует уникальный ID для момента"""
    return datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + str(random.randint(1000, 9999))

def format_date(date_str: str) -> str:
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return date_obj.strftime("%d %B %Y")

# ==================== АВТОМАТИЧЕСКОЕ СОХРАНЕНИЕ ИЗ ГРУППЫ ====================

async def auto_save_message(message: Message):
    """Автоматически сохраняет все сообщения из группы"""
    global MEMORIES
    
    try:
        # Проверяем, что сообщение из нужной группы
        if message.chat.id != GROUP_ID:
            return
        
        # Пропускаем команды бота
        if message.text and message.text.startswith('/'):
            return
        
        # Пропускаем служебные сообщения
        if message.new_chat_members or message.left_chat_member:
            return
        
        # Пропускаем сообщения от самого бота
        if message.from_user.id == (await message.bot.get_me()).id:
            return
        
        logger.info(f"📸 Автосохранение: от {message.from_user.first_name}")
        
        memory = {
            "id": generate_memory_id(),
            "date": message.date.strftime("%Y-%m-%d"),
            "time": message.date.strftime("%H:%M:%S"),
            "from_user": message.from_user.first_name,
            "username": message.from_user.username,
            "reaction": "Автоматически сохранённый момент ✨",
            "file_id": None,
            "file_path": None,
            "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "text",
            "content": ""
        }
        
        # Определяем тип сообщения
        if message.text:
            memory["type"] = "text"
            memory["content"] = message.text[:1000]
            
        elif message.voice:
            memory["type"] = "voice"
            memory["content"] = message.caption or "Голосовое сообщение 🎤"
            memory["file_id"] = message.voice.file_id
            
            file = await message.bot.get_file(message.voice.file_id)
            file_path = os.path.join(MEDIA_FOLDER, "voices", f"{memory['id']}.ogg")
            await message.bot.download_file(file.file_path, file_path)
            memory["file_path"] = file_path
            
        elif message.video_note:
            memory["type"] = "video_note"
            memory["content"] = message.caption or "Видеокружок 📹"
            memory["file_id"] = message.video_note.file_id
            
            file = await message.bot.get_file(message.video_note.file_id)
            file_path = os.path.join(MEDIA_FOLDER, "video_notes", f"{memory['id']}.mp4")
            await message.bot.download_file(file.file_path, file_path)
            memory["file_path"] = file_path
            
        elif message.video:
            memory["type"] = "video"
            memory["content"] = message.caption or "Видео 📽️"
            memory["file_id"] = message.video.file_id
            
            file = await message.bot.get_file(message.video.file_id)
            file_path = os.path.join(MEDIA_FOLDER, "videos", f"{memory['id']}.mp4")
            await message.bot.download_file(file.file_path, file_path)
            memory["file_path"] = file_path
            
        elif message.photo:
            memory["type"] = "photo"
            memory["content"] = message.caption or "Фото 📸"
            photo = message.photo[-1]
            memory["file_id"] = photo.file_id
            
            file = await message.bot.get_file(photo.file_id)
            file_path = os.path.join(MEDIA_FOLDER, "photos", f"{memory['id']}.jpg")
            await message.bot.download_file(file.file_path, file_path)
            memory["file_path"] = file_path
            
        else:
            memory["type"] = "other"
            memory["content"] = "Другое сообщение 💫"
        
        MEMORIES.append(memory)
        save_memories(MEMORIES)
        
        logger.info(f"✅ Сохранён момент: {memory['type']}")
        return memory
        
    except Exception as e:
        logger.error(f"❌ Ошибка автосохранения: {e}")
        return None

# ==================== ФУНКЦИИ ДЛЯ РАБОТЫ С МОМЕНТАМИ ====================

def get_memories_keyboard(current_index: int = 0) -> InlineKeyboardMarkup:
    """Создаёт инлайн-клавиатуру для навигации"""
    buttons = []
    
    nav_buttons = []
    if current_index > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"prev_{current_index}"))
    if current_index < len(MEMORIES) - 1:
        nav_buttons.append(InlineKeyboardButton(text="Вперёд ▶️", callback_data=f"next_{current_index}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_{current_index}")])
    buttons.append([InlineKeyboardButton(text="❌ Закрыть", callback_data="close")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def send_memory_by_index(bot: Bot, chat_id: int, index: int, reply_markup=None):
    """Отправляет памятный момент по индексу"""
    if not MEMORIES or index >= len(MEMORIES):
        await bot.send_message(chat_id, "❌ Такого момента не найдено!")
        return
    
    memory = MEMORIES[index]
    
    caption = f"📅 *{memory['date']}* в {memory.get('time', '—')}\n"
    caption += f"👤 От: {memory.get('from_user', 'неизвестно')}\n\n"
    caption += f"📝 {memory['content']}\n\n"
    caption += f"💭 {memory.get('reaction', 'Особенный момент')}\n\n"
    caption += f"📌 *{index + 1} из {len(MEMORIES)}*"
    
    try:
        if memory["type"] == "text":
            await bot.send_message(chat_id, caption, parse_mode="Markdown", reply_markup=reply_markup)
            
        elif memory["type"] == "voice" and memory.get("file_path") and os.path.exists(memory["file_path"]):
            file = FSInputFile(memory["file_path"])
            await bot.send_voice(chat_id, file, caption=caption, parse_mode="Markdown", reply_markup=reply_markup)
            
        elif memory["type"] == "video_note" and memory.get("file_path") and os.path.exists(memory["file_path"]):
            file = FSInputFile(memory["file_path"])
            await bot.send_video_note(chat_id, file)
            await bot.send_message(chat_id, caption, parse_mode="Markdown", reply_markup=reply_markup)
            
        elif memory["type"] == "photo" and memory.get("file_path") and os.path.exists(memory["file_path"]):
            file = FSInputFile(memory["file_path"])
            await bot.send_photo(chat_id, file, caption=caption, parse_mode="Markdown", reply_markup=reply_markup)
            
        else:
            await bot.send_message(chat_id, caption, parse_mode="Markdown", reply_markup=reply_markup)
            
    except Exception as e:
        logger.error(f"Ошибка при отправке: {e}")
        await bot.send_message(chat_id, f"{caption}\n\n⚠️ Ошибка загрузки", parse_mode="Markdown")

# ==================== КНОПКИ ====================

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Главная клавиатура"""
    buttons = [
        [KeyboardButton(text="📅 Дней до ДР"), KeyboardButton(text="💝 Комплимент")],
        [KeyboardButton(text="🎀 Романтичный"), KeyboardButton(text="🌿 Природный")],
        [KeyboardButton(text="🎯 Личный"), KeyboardButton(text="💪 Мотивация")],
        [KeyboardButton(text="📝 Сгенерировать 3"), KeyboardButton(text="📖 Памятный момент")],
        [KeyboardButton(text="📋 Все моменты"), KeyboardButton(text="✅ Проверить")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# ==================== КОМАНДЫ БОТА ====================

async def start_command(message: Message):
    welcome_text = (
        "🎀 Привет, мой любимый человечек! 🎀\n\n"
        "Я — твой бот с душой. ✨\n\n"
        "*Что я умею:*\n"
        "🤖 Генерировать комплименты\n"
        "💪 Поддерживать и мотивировать\n"
        "📅 Считать дни до твоего ДР\n"
        "📸 *АВТОМАТИЧЕСКИ сохранять все сообщения из группы!*\n\n"
        "Просто отправляй сообщения в нашу группу, и я сохраню их все!\n\n"
        "👇 Нажимай на кнопки ниже 👇\n\n"
        "❤️ Люблю тебя!"
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

async def days_command(message: Message):
    days = get_days_left()
    response = f"📅 До ДР осталось {days} {'день' if days == 1 else 'дней'} 💝\n\n{get_unique_compliment()}"
    await message.answer(response)

async def compliment_command(message: Message):
    await message.answer(f"✨ {get_unique_compliment()} ✨")

async def compliment_romantic_command(message: Message):
    compliment = random.choice([
        "Я искала тебя во всех людях, но нашла только в тебе. Ты — мой единственный. 💕",
        "С тобой я поняла, что значит 'жить полной жизнью'. Спасибо за каждый день. 💫",
        "Каждый день я открываю в тебе что-то новое и влюбляюсь заново. ✨",
        "Ты — мой самый любимый сон, который стал реальностью. 🌙",
        "Я люблю тебя не за что-то, а вопреки всему. ❤️"
    ])
    await message.answer(f"💕 {compliment} 💕")

async def compliment_nature_command(message: Message):
    compliment = random.choice([
        f"Ты как {random.choice(['весенний цветок', 'летний ветер', 'осенний лист', 'зимняя звезда'])} — прекрасен и уникален. 🌸",
        f"Твоя душа — как {random.choice(['океан глубиной в вечность', 'бескрайнее небо', 'чистое утро'])}. Я могу смотреть в тебя бесконечно. 💫",
        f"Твоя доброта сравнится разве что с {random.choice(['солнечным светом', 'тёплым дождём', 'первым снегом'])}. Ты согреваешь всех вокруг. ☀️"
    ])
    await message.answer(f"🌿 {compliment} 🌿")

async def compliment_personal_command(message: Message):
    nickname = random.choice(PERSONAL_NICKNAMES)
    compliment = random.choice([
        f"{nickname}, ты — мой мир! Спасибо, что ты есть. 💕",
        f"С тобой, {nickname}, даже хмурый день становится праздником. 🎉",
        f"Знаешь, {nickname}, я безумно тебя люблю! 💖"
    ])
    await message.answer(f"🎀 {compliment} 🎀")

async def motivate_command(message: Message):
    await message.answer(f"💪 {get_motivation()} 💪")

async def generate_command(message: Message):
    compliments = [f"{i+1}. {get_unique_compliment()}" for i in range(3)]
    await message.answer("📝 *Набор приятных слов:*\n\n" + "\n\n".join(compliments), parse_mode="Markdown")

async def memory_command(message: Message):
    """Случайный памятный момент"""
    if not MEMORIES:
        await message.answer("📭 Нет сохранённых моментов!\n\nОтправь сообщения в группу, и я сохраню их ✨")
        return
    
    index = random.randint(0, len(MEMORIES) - 1)
    await message.answer("📖 Ищу момент... ✨")
    await asyncio.sleep(0.5)
    await send_memory_by_index(message.bot, message.chat.id, index, get_memories_keyboard(index))

async def memories_list_command(message: Message):
    """Статистика моментов"""
    if not MEMORIES:
        await message.answer("📭 Нет сохранённых моментов")
        return
    
    types_count = {}
    for m in MEMORIES:
        t = m.get("type", "other")
        types_count[t] = types_count.get(t, 0) + 1
    
    type_names = {"text": "📝 Текстовые", "voice": "🎤 Голосовые", "video_note": "🔄 Кружки", "photo": "📸 Фото", "video": "📽️ Видео"}
    
    response = "📚 *Статистика памятных моментов*\n\n"
    response += f"📊 Всего: *{len(MEMORIES)}*\n\n"
    response += "*По типам:*\n"
    for t, count in types_count.items():
        name = type_names.get(t, t)
        response += f"  {name}: {count}\n"
    
    await message.answer(response, parse_mode="Markdown")

async def check_command(message: Message):
    await message.answer(
        f"✅ *Бот работает!*\n\n"
        f"📅 До ДР: {get_days_left()} дней\n"
        f"📸 Сохранено моментов: {len(MEMORIES)}\n"
        f"❤️ Люблю тебя!",
        parse_mode="Markdown"
    )

# ==================== CALLBACK ОБРАБОТЧИКИ ====================

async def nav_memory_callback(callback: types.CallbackQuery):
    """Навигация по моментам"""
    data = callback.data
    
    if data.startswith("prev_"):
        current = int(data.split("_")[1])
        new_index = current - 1
    elif data.startswith("next_"):
        current = int(data.split("_")[1])
        new_index = current + 1
    else:
        return
    
    if 0 <= new_index < len(MEMORIES):
        await send_memory_by_index(callback.bot, callback.message.chat.id, new_index, get_memories_keyboard(new_index))
        try:
            await callback.message.delete()
        except:
            pass
    await callback.answer()

async def delete_memory_callback(callback: types.CallbackQuery):
    """Удаление момента"""
    global MEMORIES
    
    if callback.from_user.id != USER_ID:
        await callback.answer("❌ Только создатель может удалять", show_alert=True)
        return
    
    index = int(callback.data.split("_")[1])
    if 0 <= index < len(MEMORIES):
        memory = MEMORIES[index]
        
        if memory.get("file_path") and os.path.exists(memory["file_path"]):
            try:
                os.remove(memory["file_path"])
            except:
                pass
        
        MEMORIES.pop(index)
        save_memories(MEMORIES)
        
        await callback.answer("🗑️ Момент удалён")
        
        if MEMORIES:
            new_index = min(index, len(MEMORIES) - 1)
            await send_memory_by_index(callback.bot, callback.message.chat.id, new_index, get_memories_keyboard(new_index))
            try:
                await callback.message.delete()
            except:
                pass
        else:
            try:
                await callback.message.edit_text("📭 Все моменты удалены")
            except:
                pass
    else:
        await callback.answer("❌ Момент не найден")

async def close_memory_callback(callback: types.CallbackQuery):
    """Закрытие просмотра"""
    try:
        await callback.message.delete()
    except:
        pass
    await callback.answer()

# ==================== ПЛАНИРОВЩИК ====================

async def send_daily_message(bot: Bot, user_id: int):
    try:
        days = get_days_left()
        if days == 0:
            msg = f"🎉🎂 СЕГОДНЯ ТВОЙ ДЕНЬ! 🎂🎉\n\n{SURPRISE_URL}\n\nС Днём рождения! ❤️"
        else:
            msg = f"🌅 Доброе утро! До ДР осталось {days} дней!\n\n{get_unique_compliment()}"
        await bot.send_message(user_id, msg)
        logger.info("Ежедневное сообщение отправлено")
    except Exception as e:
        logger.error(f"Ошибка: {e}")

async def daily_scheduler(bot: Bot):
    while True:
        try:
            now = datetime.now()
            target_time = now.replace(hour=10, minute=0, second=0, microsecond=0)
            if now >= target_time:
                target_time += timedelta(days=1)
            wait_seconds = (target_time - now).total_seconds()
            await asyncio.sleep(wait_seconds)
            await send_daily_message(bot, USER_ID)
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            await asyncio.sleep(60)

# ==================== ЗАПУСК ====================

async def main():
    print("=" * 60)
    print("🎀 ЗАПУСК БОТА С АВТОСОХРАНЕНИЕМ 🎀")
    print("=" * 60)
    
    print(f"\n📅 День рождения: {BIRTHDAY.strftime('%d.%m.%Y')}")
    print(f"📸 Сохранено моментов: {len(MEMORIES)}")
    print(f"👥 ID группы для автосохранения: {GROUP_ID}")
    
    if PROXY_URL:
        session = AiohttpSession(proxy=PROXY_URL)
        bot = Bot(token=TOKEN, session=session)
    else:
        bot = Bot(token=TOKEN)
    
    try:
        bot_info = await bot.get_me()
        print(f"\n✅ Бот запущен: @{bot_info.username}")
        
        dp = Dispatcher()
        
        # Регистрация обработчиков команд
        dp.message.register(start_command, Command("start"))
        dp.message.register(days_command, Command("days"))
        dp.message.register(compliment_command, Command("compliment"))
        dp.message.register(compliment_romantic_command, Command("compliment_romantic"))
        dp.message.register(compliment_nature_command, Command("compliment_nature"))
        dp.message.register(compliment_personal_command, Command("compliment_personal"))
        dp.message.register(motivate_command, Command("motivate"))
        dp.message.register(generate_command, Command("generate"))
        dp.message.register(memory_command, Command("memory"))
        dp.message.register(memories_list_command, Command("memories_list"))
        dp.message.register(check_command, Command("check"))
        
        # Регистрация обработчиков текстовых кнопок (должны быть зарегистрированы до auto_save_message)
        @dp.message(lambda m: m.text == "📅 Дней до ДР")
        async def btn_days(m: Message): await days_command(m)
        
        @dp.message(lambda m: m.text == "💝 Комплимент")
        async def btn_compliment(m: Message): await compliment_command(m)
        
        @dp.message(lambda m: m.text == "🎀 Романтичный")
        async def btn_romantic(m: Message): await compliment_romantic_command(m)
        
        @dp.message(lambda m: m.text == "🌿 Природный")
        async def btn_nature(m: Message): await compliment_nature_command(m)
        
        @dp.message(lambda m: m.text == "🎯 Личный")
        async def btn_personal(m: Message): await compliment_personal_command(m)
        
        @dp.message(lambda m: m.text == "💪 Мотивация")
        async def btn_motivate(m: Message): await motivate_command(m)
        
        @dp.message(lambda m: m.text == "📝 Сгенерировать 3")
        async def btn_generate(m: Message): await generate_command(m)
        
        @dp.message(lambda m: m.text == "📖 Памятный момент")
        async def btn_memory(m: Message): await memory_command(m)
        
        @dp.message(lambda m: m.text == "📋 Все моменты")
        async def btn_list(m: Message): await memories_list_command(m)
        
        @dp.message(lambda m: m.text == "✅ Проверить")
        async def btn_check(m: Message): await check_command(m)
        
        # АВТОСОХРАНЕНИЕ (регистрируем последним, чтобы не перехватывало кнопки)
        dp.message.register(auto_save_message)
        
        # Callback обработчики
        dp.callback_query.register(nav_memory_callback, lambda c: c.data.startswith(("prev_", "next_")))
        dp.callback_query.register(delete_memory_callback, lambda c: c.data.startswith("delete_"))
        dp.callback_query.register(close_memory_callback, lambda c: c.data == "close")
        
        # Запускаем планировщик
        asyncio.create_task(daily_scheduler(bot))
        
        print("\n✨ Бот готов!")
        print("=" * 60)
        print("📸 АВТОСОХРАНЕНИЕ АКТИВНО!")
        print("   Все сообщения из группы будут сохраняться автоматически")
        print("   Для просмотра используйте кнопку '📖 Памятный момент'")
        print("=" * 60)
        
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        print(f"\n❌ Ошибка: {e}")
    finally:
        if bot:
            await bot.session.close()

if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n✨ Бот остановлен.")