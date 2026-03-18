# Schema: Описание полей медиакорпуса

Версия: 1.0
Дата: 2024

---

## Обязательные поля для каждого материала

### Идентификация

| Поле | Тип | Описание |
|------|-----|----------|
| `case_id` | string | Идентификатор кейса (redsea_shipping, boeing_crisis, etc.) |
| `material_id` | string | Уникальный ID материала (UUID или hash) |

### Источник

| Поле | Тип | Описание |
|------|-----|----------|
| `source_name` | string | Название источника (Reuters, РБК, ТАСС, etc.) |
| `source_country` | string | Страна источника (US, RU, UK, DE, etc.) |
| `source_language` | string | Язык материала (en, ru, etc.) |
| `source_block` | enum | Блок источника: `international` / `russian` / `official` |
| `source_type` | enum | Тип источника: `news_agency` / `newspaper` / `tv` / `digital` / `official` / `social` |

### Временные метки

| Поле | Тип | Описание |
|------|-----|----------|
| `published_at` | datetime | Дата и время публикации (ISO 8601) |
| `collected_at` | datetime | Дата и время сбора материала |

### Содержание

| Поле | Тип | Описание |
|------|-----|----------|
| `title` | string | Заголовок материала |
| `url` | string | URL материала |
| `description` | text | Краткое описание / лид |
| `content` | text | Полный текст (если доступен) |
| `author` | string | Автор (если указан) |

### Методология сбора

| Поле | Тип | Описание |
|------|-----|----------|
| `query_used` | string | Запрос, по которому найден материал |
| `window` | enum | Временное окно: `year` / `3m` / `1m` / `post` |
| `collection_method` | enum | Метод сбора: `newsapi` / `rss` / `web_search` / `manual` |

---

## Аналитические поля (разметка)

### Нарративная стадия

| Поле | Тип | Описание |
|------|-----|----------|
| `narrative_stage` | enum | Стадия нарратива: `N0` / `N1` / `N2` / `N3` / `N4` / `N5` |

**Расшифровка стадий:**
- **N0** — нормальное присутствие объекта в медиаполе
- **N1** — слабая проблематизация, единичные сигналы
- **N2** — устойчивая проблематизация, рост внимания
- **N3** — персонализация вины/ответственности
- **N4** — системный кризис/угроза
- **N5** — развязка/стабилизация/переопределение

### Тональность и тревожность

| Поле | Тип | Описание |
|------|-----|----------|
| `sentiment` | enum | Общая тональность: `negative` / `neutral` / `positive` / `mixed` |
| `anxiety_level` | integer | Уровень тревожности: `0` (нет) / `1` (низкий) / `2` (средний) / `3` (высокий) |

### Рамки и фрейминг

| Поле | Тип | Описание |
|------|-----|----------|
| `frame_type` | enum | Тип рамки: `legal` / `managerial` / `economic` / `political` / `humanitarian` / `sport` / `medical` / `security` |
| `blame_present` | boolean | Присутствует ли обвинение: `true` / `false` |
| `blame_target` | string | Объект обвинения (если есть) |
| `systemic_risk` | boolean | Присутствует ли системный риск: `true` / `false` |

### Краткое резюме

| Поле | Тип | Описание |
|------|-----|----------|
| `brief_summary_3_sentences` | text | Краткое резюме материала (3 предложения) |

---

## Служебные поля

| Поле | Тип | Описание |
|------|-----|----------|
| `dedup_key` | string | Ключ дедупликации (hash от title + date + source) |
| `relevance_score` | float | Оценка релевантности (0-1) |
| `is_duplicate` | boolean | Флаг дубликата |
| `duplicate_of` | string | ID оригинала (если дубликат) |
| `needs_manual_review` | boolean | Требует ручной проверки |
| `review_notes` | text | Заметки рецензента |

---

## Пример записи

```json
{
  "case_id": "june2023_events",
  "material_id": "abc123",
  "source_name": "Reuters",
  "source_country": "UK",
  "source_language": "en",
  "source_block": "international",
  "source_type": "news_agency",
  "published_at": "2023-06-24T10:30:00Z",
  "title": "События июня 2023, Russian military helicopters fire on convoy",
  "url": "https://reuters.com/...",
  "description": "Руководитель частной военной структуры...",
  "query_used": "Кейс 4 mutiny Russia June 2023",
  "window": "1m",
  "collection_method": "newsapi",
  "narrative_stage": "N4",
  "sentiment": "negative",
  "anxiety_level": 3,
  "frame_type": "security",
  "blame_present": true,
  "blame_target": "Russian military leadership",
  "systemic_risk": true,
  "brief_summary_3_sentences": "Руководитель структуры объявил armed mutiny against Russian military leadership. Russian forces opened fire on Кейс 4 convoy approaching Moscow. The rebellion ended within 24 hours after negotiations mediated by Belarus."
}
```
