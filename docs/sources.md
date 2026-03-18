# Sources: Список источников медиакорпуса

Версия: 1.0
Дата: 2024

---

## 1. Международные источники

### 1.1. Глобальные новостные агентства

| Источник | Страна | Язык | Тип | Доступ |
|----------|--------|------|-----|--------|
| Reuters | UK | en | news_agency | NewsAPI |
| AP (Associated Press) | US | en | news_agency | NewsAPI |
| AFP (Agence France-Presse) | FR | fr/en | news_agency | NewsAPI |
| Bloomberg | US | en | news_agency | NewsAPI |
| BBC News | UK | en | news_agency | NewsAPI |

### 1.2. Американские СМИ

| Источник | Тип | Доступ |
|----------|-----|--------|
| The New York Times | newspaper | NewsAPI |
| The Washington Post | newspaper | NewsAPI |
| CNN | tv/digital | NewsAPI |
| NPR | radio/digital | NewsAPI |
| Axios | digital | NewsAPI |
| The Wall Street Journal | newspaper | NewsAPI |
| CNBC | tv/digital | NewsAPI |
| TechCrunch | digital | NewsAPI |

### 1.3. Европейские СМИ

| Источник | Страна | Тип | Доступ |
|----------|--------|-----|--------|
| The Guardian | UK | newspaper | NewsAPI |
| Financial Times | UK | newspaper | NewsAPI |
| Der Spiegel | DE | magazine | NewsAPI |
| Al Jazeera | QA | tv/digital | NewsAPI |

### 1.4. Официальные источники

| Источник | Тип | URL |
|----------|-----|-----|
| WHO | official | who.int |
| FAA | official | faa.gov |
| NTSB | official | ntsb.gov |
| US Congress | official | congress.gov |
| Supreme Court | official | supremecourt.gov |
| IPC | official | paralympic.org |

---

## 2. Российские источники

### 2.1. Федеральные новостные агентства

| Источник | Тип | Доступ |
|----------|-----|--------|
| ТАСС | news_agency | RSS, NewsAPI |
| РИА Новости | news_agency | RSS, NewsAPI |
| Интерфакс | news_agency | RSS, NewsAPI |
| РБК | news_agency | RSS, NewsAPI |

### 2.2. Деловые и экономические СМИ

| Источник | Тип | Доступ |
|----------|-----|--------|
| Коммерсант | newspaper | RSS, NewsAPI |
| Ведомости | newspaper | RSS, NewsAPI |
| Forbes.ru | digital | RSS |
| Российская газета | newspaper | RSS |

### 2.3. Специализированные источники

**Спорт:**
| Источник | Тип | Доступ |
|----------|-----|--------|
| Матч ТВ | tv/digital | Web |
| Чемпионат | digital | Web |
| Спорт-Экспресс | newspaper/digital | Web |

**Медицина:**
| Источник | Тип | Доступ |
|----------|-----|--------|
| Медицинский вестник | digital | Web |
| Remedium | digital | Web |

**Технологии:**
| Источник | Тип | Доступ |
|----------|-----|--------|
| VC.ru | digital | RSS |
| Хабр | digital/community | Web |

**Логистика/Транспорт:**
| Источник | Тип | Доступ |
|----------|-----|--------|
| Логистика.ru | industry | Web |
| Морские вести | industry | Web |

### 2.4. Официальные источники

| Источник | Тип | URL |
|----------|-----|-----|
| Минсельхоз РФ | official | mcx.gov.ru |
| Минспорт РФ | official | minsport.gov.ru |
| Росстат | official | rosstat.gov.ru |
| ПКР | official | paralymp.ru |
| Следственный комитет | official | sledcom.ru |

---

## 3. Источники по кейсам

### 3.1. Красное море / судоходство

**Международные:**
- Lloyd's List (морская отрасль)
- The Maritime Executive
- Shipping press
- USNI News

**Российские:**
- ПортНьюс
- Морские вести России
- РЖД-Партнёр

### 3.2. Boeing

**Международные:**
- Aviation Week
- FlightGlobal
- Air Transport World

**Российские:**
- АвиаПорт
- Aviation Explorer

### 3.3. TikTok

**Международные:**
- Tech media (TechCrunch, The Verge)
- Policy outlets

**Российские:**
- VC.ru
- RB.ru
- Цифровые СМИ

### 3.4. События июня 2023

**Международные:**
- Defense analysts
- Conflict reporting

**Российские:**
- Федеральные каналы
- Новостные агентства
- Телеграм-каналы (аналитические)

### 3.5. Яичный кризис

**Российские (основной блок):**
- РБК
- Коммерсант
- Ведомости
- Региональные СМИ
- Отраслевые издания

### 3.6. FESCO

**Российские (основной блок):**
- РБК
- Коммерсант
- Forbes.ru
- Отраслевые логистические издания

### 3.7. Wildberries

**Российские (основной блок):**
- РБК
- Ведомости
- Forbes.ru
- Известия
- Коммерсант

### 3.8. OpenAI

**Международные:**
- Tech media
- Business press
- AI specialists

**Российские:**
- VC.ru
- Хабр
- РБК Тренды

### 3.9. Паралимпиада-2024

**Международные:**
- IPC official
- Sports press

**Российские:**
- Матч ТВ
- Чемпионат
- ТАСС Спорт
- ПКР официальный

### 3.10. Mpox

**Международные:**
- WHO official
- CDC
- Medical journals
- Global health press

**Российские:**
- Роспотребнадзор
- Медицинские издания
- РИА Новости (здоровье)

---

## 4. Методы доступа

| Метод | Источники | Ограничения |
|-------|-----------|-------------|
| NewsAPI | Международные, некоторые российские | Лимит запросов |
| RSS | Российские, некоторые международные | Бесплатно |
| Web Search | Все | Требует обработки |
| Официальные сайты | Официальные источники | Бесплатно |

---

## 5. Фильтры качества

### 5.1. Критерии включения

- Авторитетность источника
- Релевантность кризисной рамке
- Наличие даты публикации
- Уникальность контента

### 5.2. Критерии исключения

- Явные перепечатки без добавленной ценности
- Рекламные материалы
- Нерелевантные упоминания (омонимия)
- Отсутствие существенного содержания
