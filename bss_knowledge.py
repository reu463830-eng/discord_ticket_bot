import re

BSS_QA = [
    {
        "keywords": ["тир", "tier", "лучшие пчелы", "топ пчел", "рейтинг", "какая пчела лучше", "самая сильная"],
        "answer": "🏆 **Тир-лист пчёл BSS (2026)**\n\nS-тир: Vector Bee, Gummy Bee, Fuzzy Bee, Tadpole Bee, Vicious Bee, Festive Bee\n\nA-тир: Spicy Bee, Precise Bee, Cobalt Bee, Crimson Bee, Tabby Bee, Photon Bee, Windy Bee, Buoyant Bee\n\nB-тир: Lion Bee, Bear Bee, Ninja Bee, Carpenter Bee, Riley Bee, Bucko Bee, Diamond Bee, Rage Bee\n\nC-тир: Honey Bee, Brave Bee, Hasty Bee, Bumble Bee, Exhausted Bee\n\nD-тир (меняй сразу): Basic Bee, Bomber Bee, Looker Bee",
    },
    {
        "keywords": ["red hive", "красный улей", "red build", "красный билд", "поля красного", "где фармить красный"],
        "answer": "🔴 **Красный улей**\n\n✅ Лучшие поля: Rose Field, Strawberry Field, Mushroom Field, Cactus Field, Pepper Patch, Pumpkin Patch\n\n❌ Bamboo — это БЕЛОЕ поле, НЕ для красного!\n\nЭндгейм билд: 11x Precise Bee Gifted, 4-8x Vector Bee Gifted, 10x Spicy Bee Gifted, Crimson Bee Gifted, Vicious Bee, Festive Bee Gifted, Tabby Bee Gifted, Photon Bee, 2x Tadpole Bee Gifted, Riley Bee Gifted\n\nАмулеты: Supreme Star, Silver Ant, Diamond Stick Bug, Supreme Cog",
    },
    {
        "keywords": ["blue hive", "синий улей", "blue build", "синий билд", "поля синего", "где фармить синий"],
        "answer": "🔵 **Синий улей**\n\n✅ Лучшие поля: Blue Flower Field, Bamboo Field, Pineapple Patch, Pine Tree Forest, Coconut Field\n\nЯкорная пчела: Gifted Bucko Bee (+20% ёмкости синего поля)\n\nКлючевые пчёлы: Cobalt Bee, Buoyant Bee, Vicious Bee, Ninja Bee, Diamond Bee, Cool Bee, Frosty Bee, Bumble Bee",
    },
    {
        "keywords": ["white hive", "белый улей", "white build", "белый билд", "поля белого", "где фармить белый"],
        "answer": "⚪ **Белый улей**\n\n✅ Лучшие поля: Clover Field, Bamboo Field, Sunflower Field, Dandelion Field, Mountain Top Field (эндгейм)\n\nЯкорная пчела: Gifted Exhausted Bee (+20% ёмкости белого поля)\n\nКлючевые пчёлы: Tabby Bee Gifted, Photon Bee, Windy Bee Gifted, Gummy Bee Gifted, Honey Bee, Shocked Bee",
    },
    {
        "keywords": ["mixed hive", "смешанный улей", "новичок улей", "clover", "клевер", "beginner hive"],
        "answer": "🌈 **Смешанный улей**\n\nЛучшее поле: Clover Field — красные + синие + белые цветы, работает для любого цвета пчёл.\n\nПосле 10-15 пчёл посмотри какой цвет доминирует и иди в ту сторону.\n\nГлавная ошибка: тратить Royal Jelly на пчёл трёх цветов — разбавляешь все три бонуса!",
    },
    {
        "keywords": ["начало", "новичок", "начать", "стартовый", "с чего начать", "beginner", "гайд новичка", "первые шаги"],
        "answer": "🚀 **Гайд для новичков BSS**\n\n1. Старт на Clover Field — лучшее для начала\n2. Выполни квесты Black Bear у спавна — даёт 2.35 млрд мёда суммарно!\n3. Получи 5 пчёл → открой 5 Bee Gate (Bamboo, Spider, Strawberry)\n4. Получи Brave Bee → открой Brave Bee Gate (Pineapple, Stump, Cactus)\n5. Получи Honey Bee → открой Honey Bee Gate (Rose Field!)\n6. Купи Tabby Bee в Ticket Shop — высший приоритет!\n\nВведи коды сразу: FOURtunate и ThreeBeeVee — дают Marshmallow Bee!\nВорота открываются НЕ за билеты — за наличие нужных пчёл!",
    },
    {
        "keywords": ["мид гейм", "mid game", "10 пчел", "20 пчел", "30 пчел", "средний уровень", "прогрессия"],
        "answer": "⚔️ **Мид-гейм (10-30 пчёл)**\n\n1. Определись с цветом улья и придерживайся его!\n2. Прокачай Tabby Bee — начни качать стаки как можно раньше\n3. Riley Bee (красный) или Bucko Bee (синий) — якорные пчёлы\n4. Получи Gummy Bee — нужна для Spirit Bear!\n5. Квесты Science Bear — очки исследования дают постоянные бонусы\n\nRoyal Jelly: трать регулярно, не копи — 1/287 шанс Gifted\nЦель: Gold Egg для Mythic пчёл",
    },
    {
        "keywords": ["эндгейм", "endgame", "лейт", "late game", "50 пчел", "топ игроки", "максимальный прогресс"],
        "answer": "👑 **Эндгейм прогрессия**\n\n4 главные цели:\n1. Gummy Bee → открывает Spirit Bear\n2. Windy Bee → открывает Windy Bee Gate\n3. Precise Bee Gifted — +3% супер-крит\n4. Gifted Mythic: Vector, Fuzzy, Spicy, Tadpole\n\nStar Jelly — гарантированный Gifted. ТОЛЬКО на Mythic/Legendary, НЕ на Rare!\n\nЭндгейм поля:\nRed: Rose Field, Pepper Patch\nBlue: Pineapple Patch, Coconut Field\nWhite: Mountain Top Field",
    },
    {
        "keywords": ["spirit bear", "спирит", "gummy bee нужна", "как открыть spirit"],
        "answer": "👻 **Spirit Bear**\n\nТребование: иметь Gummy Bee — жёсткое условие, обхода нет!\n\nGummy Bee конвертирует 700 мёда за поездку + Gifted бонус +5% мёда с пыльцы.\n\nАктивно охоться за Gummy Bee после основных квестов Black Bear — это ключ к эндгейм контенту.",
    },
    {
        "keywords": ["black bear", "квесты медведя", "black bear rewards", "с чего начать квесты"],
        "answer": "🐻 **Black Bear**\n\nНаходится у спавна. Первый и важнейший медведь.\n\nЦепочка наград: Silver Egg → Gold Egg → Diamond Egg → Star Jelly → Mythic Egg\nСуммарно даёт 2.35 миллиарда мёда и 5 Royal Jelly!\n\nНЕ ПРОПУСКАЙ ни одного квеста — это основа твоей экономики.",
    },
    {
        "keywords": ["science bear", "научный медведь", "research", "исследование", "очки исследования"],
        "answer": "🔬 **Science Bear**\n\nДаёт квесты за которые ты получаешь очки исследования.\nОчки дают постоянные бонусы к улью — пыльца, конвертация, атака.\n\nВыполняй квесты Science Bear параллельно с Black Bear и Brown Bear — один из важнейших аспектов прогрессии!",
    },
    {
        "keywords": ["ворота", "gate", "5 bee gate", "brave bee gate", "honey bee gate", "windy bee gate", "открыть зону"],
        "answer": "🚪 **Ворота BSS**\n\nВорота открываются НЕ за билеты — за наличие пчёл!\n\n• 5 Bee Gate — иметь 5 пчёл → Bamboo, Spider, Strawberry Field, Panda Bear\n• Brave Bee Gate — иметь Brave Bee → Pineapple Patch, Stump Field, Cactus Field\n• Honey Bee Gate — иметь Honey Bee → Rose Field, Pumpkin Patch, Pine Tree Forest\n• Windy Bee Gate — иметь Windy Bee → эндгейм зоны\n\nПервая цель: 5 пчёл и Brave Bee как можно скорее!",
    },
    {
        "keywords": ["gifted", "гифтед", "как получить gifted", "шанс gifted", "star jelly", "royal jelly gifted"],
        "answer": "🎁 **Gifted пчёлы**\n\nШансы через любимое угощение:\n• Rare — 1/8000\n• Epic — 1/10000\n• Legendary/Common — 1/12000\n• Mythic — 1/24000\n\nЧерез Royal Jelly: 1/287 (0.35%) — реалистичный путь!\nStar Jelly — ГАРАНТИРОВАННЫЙ Gifted!\n\nНЕ трать Star Jelly на Rare — только на Legendary или Mythic!\nЛучшая стратегия: трать Royal Jelly регулярно, не копи.",
    },
    {
        "keywords": ["tabby", "тэбби", "tabby bee", "tabby love", "стаки тэбби", "1000 стаков"],
        "answer": "🐱 **Tabby Bee — A-тир**\n\nEnergy: 28, Speed: 16.1, Attack: 4\n\nTabby Love токены — постоянно улучшают сбор и конвертацию на 1% за стак (макс 1000)\nПри 1000 стаках: 20 пыльцы/4сек и 1760 мёда/3сек!\n\nGifted бонус: +50% силы крита для всего улья\n\nПолучить: Ticket Shop за билеты — ПЕРВЫЙ ПРИОРИТЕТ покупки!\nЧем раньше начнёшь качать стаки — тем лучше.",
    },
    {
        "keywords": ["photon", "фотон", "photon bee", "бесконечная энергия", "beamstorm"],
        "answer": "⚡ **Photon Bee — A-тир**\n\nЭнергия: БЕСКОНЕЧНАЯ — никогда не устаёт!\nСкорость: 21 — одна из быстрейших\nGifted бонус: +5% моментальной конвертации для всего улья\n\nПодходит для любого типа улья. Никогда не спит.",
    },
    {
        "keywords": ["vector", "вектор", "vector bee", "самая высокая атака", "triangulate"],
        "answer": "📐 **Vector Bee (Mythic) — #1 пчела**\n\nАтака: 45 — максимальная в игре!\nЭнергия: 45.6, Скорость: 16.24\n\nСпособность Triangulate: треугольники между токеном, пчелой и игроком — собирает с всех цветов внутри\nGifted бонус: +15% длительности меток\n\nВ топ красном билде нужно 4-8x Vector Bee Gifted.",
    },
    {
        "keywords": ["fuzzy", "фаззи", "fuzzy bee", "100 пыльцы", "pollen haze", "fuzz bombs"],
        "answer": "🟡 **Fuzzy Bee (Mythic) — S-тир**\n\nСбор: 100 пыльцы за действие — в 10 раз больше базовой!\nFuzz Bombs — 2+ странствующих бомбы по 29 цветов каждая\nGifted Pollen Haze: 30сек, 30 цветов/сек по всему полю!\nGifted бонус: +10% мощности бомб\n\nИдеальна для белого улья — Bamboo Field + Fuzzy Bee = огромная пыльца.",
    },
    {
        "keywords": ["vicious", "вишес", "vicious bee", "9 атаки", "impale"],
        "answer": "🔴 **Vicious Bee (Event) — S-тир**\n\nАтака: 9, Скорость: 17.5, Энергия: 50\nСиняя пчела! Хороша и для синего улья тоже\nСпособность Impale — мощная атака по мобам\nGifted бонус: -15% времени респауна монстров\n\nЛучшая для фарма мобов, боссов, Robo Bear Challenge.",
    },
    {
        "keywords": ["riley", "riley bee", "bucko", "bucko bee", "якорная пчела", "ёмкость поля", "capacity"],
        "answer": "🔑 **Riley и Bucko Bee — якорные пчёлы**\n\nRiley Bee (Epic) — для красного улья:\nGifted: +20% ёмкости красного поля\nСоздаёт Riley's Royal Jelly\n\nBucko Bee (Epic) — для синего улья:\nGifted: +20% ёмкости синего поля\n\nПолучи нужную якорную пчелу своего цвета как можно раньше!\nВ эндгейме заменяются на Crimson/Cobalt Bee.",
    },
    {
        "keywords": ["код", "code", "коды", "promo", "промокод", "redeem", "коды 2026"],
        "answer": "🎟️ **Промокоды BSS (2026)**\n\nВводятся в меню Codes в игре.\n\n• FOURtunate — Marshmallow Bee + куча предметов\n• ThreeBeeVee — Marshmallow Bee + Loaded Dice + Mountain Top Code\n• 38217 — 5 билетов\n• Bopmaster — 5 билетов\n• Nectar — 5000 мёда\n• Wax — 5 билетов + 5000 мёда\n• Buzz, Cog, Troggles, Jumpstart, Dinner, Wink — бустеры\n\nСледи за Twitter/Discord Onett для новых кодов!",
    },
    {
        "keywords": ["мёд", "honey", "как фармить", "много меда", "фарм", "honey per hour"],
        "answer": "🍯 **Как фармить много мёда**\n\nНовичок: Clover Field + все квесты Black Bear + качай стаки Tabby Bee\n\nМид-гейм: поле своего цвета улья\nRed: Rose Field | Blue: Pineapple Patch | White: Bamboo/Mountain Top\n\nЭндгейм:\n• Tabby Bee 1000 стаков = x2 ко всему\n• Festive Bee Gifted = x1.25 конвертация\n• Vector марки + Fuzzy Pollen Haze\n\nНе трать мёд зря — копи на Gold Egg и слоты!",
    },
    {
        "keywords": ["royal jelly", "роял желе", "когда использовать rj", "на кого тратить rj"],
        "answer": "👑 **Royal Jelly**\n\nКонвертирует пчелу в случайную той же редкости (не Common, не Event).\nШанс Gifted: 1/287 (0.35%)\n\nИспользуй когда:\n— хочешь переролить слот\n— есть дублирующиеся пчёлы (2 одинаковых = лишняя)\n— накопил запас — RJ нужно тратить, не копить!\n\nНЕ спамь RJ в надежде получить конкретную пчелу — результат случайный\nНЕ трать Star Jelly на Rare!",
    },
    {
        "keywords": ["пчела", "bee", "виды пчел", "типы пчел", "редкость", "rarity", "какие пчелы есть"],
        "answer": "🐝 **Пчёлы в BSS**\n\nВсего 50+ уникальных пчёл по редкостям:\n• Common: Basic Bee\n• Rare: Brave, Bumble, Hasty, Rascal, Rad, Cool, Frosty...\n• Epic: Honey Bee, Riley, Bucko, Carpenter, Commander, Shocked, Exhausted...\n• Legendary: Lion, Diamond, Ninja, Baby, Demon, Music, Shy...\n• Mythic: Fuzzy, Photon, Spicy, Precise, Vector, Buoyant, Tadpole\n• Event: Tabby, Vicious, Festive, Gummy, Cobalt, Crimson, Windy, Bear, Puppy, Digital\n\nПчёлы делятся по цвету: синие, красные и белые (colorless).\nСиние/красные собирают на 50% больше пыльцы с цветов своего цвета.",
    },
    {
        "keywords": ["билеты", "ticket", "на что тратить", "ticket shop", "приоритет"],
        "answer": "🎟️ **Билеты — на что тратить**\n\nПриоритет:\n1. Royal Jelly — лучшая отдача в начале/мид-гейме\n2. Tabby Bee — первая ивентовая пчела\n3. Vicious Bee / Gummy Bee\n4. Festive Bee — только во время Beesmas\n\nНЕ трать билеты на обычные предметы — береги на Royal Jelly и пчёл!",
    },
    {
        "keywords": ["бафф", "buff", "баффы", "стак", "stack", "precision", "прецижн", "focus", "мотивация", "motivation"],
        "answer": "✨ **Баффы BSS**\n\n• Precision — сбор пыльцы, стак до 10x\n• Focus — сбор пыльцы, стак до 10x\n• Motivation — скорость пчёл, стак до 10x\n• Haste — скорость движения игрока\n• Bee Attack — урон пчёл\n• Critical Chance — шанс крита\n• Super-Crit Chance — шанс супер-крита\n• Loot Luck — качество лута с мобов\n\nДержи Precision и Focus на 10x стаках для максимального фарма!",
    },
    {
        "keywords": ["амулет", "amulet", "supreme star", "silver ant", "moon amulet"],
        "answer": "💍 **Лучшие амулеты BSS**\n\nДля красного улья:\n• Supreme Star Amulet — Scorching Star + Star Saw пассивы\n• Silver Ant Amulet — +атака, +красная пыльца, +крит\n• Diamond Stick Bug Amulet — +атака, +красная пыльца\n• Supreme Cog Amulet — +атака, +пыльца от способностей\n• King Beetle Amulet — +атака\n\nУниверсальные:\n• Moon Amulet — +пыльца, +связь с угощениями\n\nСтаты случайные — ищи нужные бонусы к типу улья!",
    },
    {
        "keywords": ["beequip", "бикип", "beequips", "предмет для пчелы", "украшение"],
        "answer": "🎀 **Beequips для топ красного билда**\n\n• Toy Horn → Crimson Bee, Rage Bee\n• Toy Drum → Riley Bee\n• Paper Angel → Photon Bee\n• Beesmas Top → Hasty Bee, Brave Bee, Basic Bee\n• Beesmas Tree Hat → Precise Bees\n• Bubble Light → Vector Bee\n• Sweatband → Digital Bee\n• Poinsettia → Tadpole Bee\n• Peppermint Antennas → Bear Bee\n\nПолучить: из мобов, боссов, квестов, Polar Bear крафт.",
    },
    {
        "keywords": ["поле", "field", "поля", "где фармить", "какое поле", "bamboo", "rose", "pineapple", "clover", "sunflower"],
        "answer": "🌸 **Поля BSS**\n\nБесплатные с начала: Sunflower, Dandelion, Mushroom, Blue Flower, Clover\n\nПосле 5 Bee Gate: Bamboo (белое ✅), Spider, Strawberry (красное)\n\nПосле Brave Bee Gate: Pineapple Patch (синее ✅), Stump Field, Cactus Field\n\nПосле Honey Bee Gate: Rose Field (красное ✅), Pumpkin Patch, Pine Tree Forest\n\nЭндгейм:\n• Red: Pepper Patch, Pumpkin Patch\n• Blue: Pineapple Patch, Coconut Field\n• White: Mountain Top Field\n\nКлевер — лучшее для смешанного/начального улья (все три цвета цветков).",
    },
]

DEFAULT_ANSWER = (
    "🤔 Не нашёл точного ответа.\n\n"
    "Попробуй конкретнее:\n"
    "• лучшие поля для красного улья\n"
    "• гайд для новичка\n"
    "• что такое tabby bee\n"
    "• как получить gifted пчелу\n\n"
    "Или загляни на вики: https://bee-swarm-simulator.fandom.com/wiki/Bee_Swarm_Simulator_Wiki"
)


def find_answer(question: str) -> str:
    q = question.lower()
    q_words = set(re.sub(r"[^\w\s]", "", q).split())
    best = None
    best_score = 0
    for entry in BSS_QA:
        score = 0
        for kw in entry["keywords"]:
            kw_lower = kw.lower()
            if kw_lower in q:
                score += 3
            else:
                kw_words = set(kw_lower.split())
                score += len(kw_words & q_words)
        if score > best_score:
            best_score = score
            best = entry
    if best and best_score >= 1:
        return best["answer"]
    return DEFAULT_ANSWER

# Дополнительные записи добавляются в список
BSS_QA += [
    {
        "keywords": ["vector", "вектор", "vector bee", "самая высокая атака", "triangulate"],
        "answer": "📐 **Vector Bee (Mythic) — #1 пчела в игре**\n\nАтака: 45 — максимальная в игре!\nЭнергия: 45.6, Скорость: 16.24\n\nСпособность Triangulate: рисует треугольники между токеном, пчелой и игроком — собирает пыльцу со всех цветов внутри треугольника.\nGifted бонус: +15% длительности меток\n\nВ топ красном билде нужно 4-8x Vector Bee Gifted.\nНезаменима для эндгейма в любом улье.",
    },
]
