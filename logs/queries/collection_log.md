# Логи запросов: NewsAPI и Web Search

**Дата:** 2024

---

## NewsAPI Collection (международные источники)

### Case 1: Красное море

| Файл | Query | Window | Результатов |
|------|-------|--------|-------------|
| redsea_3m_search1.json | Red Sea Houthi attacks shipping crisis November December 2023 January 2024 | 3m | 10 |
| redsea_3m_search2.json | Houthi missiles Red Sea vessels attacked Suez Canal 2024 | 3m | 10 |
| redsea_year_search1.json | Red Sea shipping attacks early warning signals October 2023 | year | 10 |
| redsea_ru_search1.json | Красное море хуситы атаки суда кризис 2024 | russian | 10 |

### Case 2: Boeing

| Файл | Query | Window | Результатов |
|------|-------|--------|-------------|
| boeing_1m_search1.json | Boeing 737 MAX door plug Alaska Airlines January 2024 crisis | 1m | 10 |
| boeing_1m_search2.json | Boeing quality issues safety problems FAA investigation 2024 | 1m | 10 |
| boeing_year_search1.json | Boeing 737 MAX problems 2023 production issues whistleblower | year | 10 |

### Case 3: TikTok

| Файл | Query | Window | Результатов |
|------|-------|--------|-------------|
| tiktok_1m_search1.json | TikTok ban Congress March 2024 ByteDance law | 1m | 10 |

### Case 4: Вагнер

| Файл | Query | Window | Результатов |
|------|-------|--------|-------------|
| wagner_1m_search1.json | Wagner Prigozhin mutiny Russia June 23 24 2023 rebellion | 1m | 10 |
| wagner_3m_search1.json | Prigozhin Shoigu conflict May June 2023 Wagner Russia | 3m | 10 |

### Case 5: Яичный кризис

| Файл | Query | Window | Результатов |
|------|-------|--------|-------------|
| eggs_1m_search1.json | Russia egg prices shortage December 2023 crisis inflation | 1m | 10 |

### Case 6: FESCO

| Файл | Query | Window | Результатов |
|------|-------|--------|-------------|
| fesco_1m_search1.json | FESCO Severilov arrest February 2026 Russia embezzlement | 1m | 10 |

### Case 7: Wildberries

| Файл | Query | Window | Результатов |
|------|-------|--------|-------------|
| wildberries_1m_search1.json | Wildberries Bakalchuk conflict September 2024 shooting office Moscow | 1m | 10 |

### Case 8: OpenAI

| Файл | Query | Window | Результатов |
|------|-------|--------|-------------|
| openai_1m_search1.json | OpenAI Sam Altman fired reinstated November 2023 CEO crisis | 1m | 10 |

### Case 9: Паралимпиада

| Файл | Query | Window | Результатов |
|------|-------|--------|-------------|
| paralympics_1m_search1.json | Paralympics 2024 Russia NPA neutral flag IPC March August | 1m | 10 |

### Case 10: Mpox

| Файл | Query | Window | Результатов |
|------|-------|--------|-------------|
| mpox_1m_search1.json | Mpox monkeypox WHO emergency August 2024 outbreak Africa | 1m | 10 |

---

## Russian Media Collection

### Case 1: Красное море

| Файл | Query | Результатов |
|------|-------|-------------|
| redsea_ru.json | Красное море судоходство хуситы влияние Россия 2024 | 10 |

### Case 2: Boeing

| Файл | Query | Результатов |
|------|-------|-------------|
| boeing_tass.json | ТАСС Boeing 737 MAX инцидент январь 2024 | 10 |

### Case 4: Вагнер

| Файл | Query | Результатов |
|------|-------|-------------|
| wagner_rbc.json | РБК Вагнер Пргоожин мятеж июнь 2023 | 10 |
| wagner_tass.json | Интерфакс FESCO Северилов арест | 10 |

### Case 5: Яичный кризис

| Файл | Query | Результатов |
|------|-------|-------------|
| eggs_kommersant.json | Коммерсант яйца подорожание Россия дефицит 2023 | 10 |
| eggs_rosstat.json | Росстат яйца цены рост декабрь 2023 | 10 |

### Case 6: FESCO

| Файл | Query | Результатов |
|------|-------|-------------|
| fesco_interfax.json | Интерфакс FESCO Северилов арест | 10 |

### Case 7: Wildberries

| Файл | Query | Результатов |
|------|-------|-------------|
| wildberries_vedomosti.json | Ведомости Wildberries конфликт Бакальчук | 10 |

### Case 9: Паралимпиада

| Файл | Query | Результатов |
|------|-------|-------------|
| paralympics_pcr.json | Паралимпийский комитет России NPA нейтральный флаг 2024 | 10 |

### Case 10: Mpox

| Файл | Query | Результатов |
|------|-------|-------------|
| mpox_rospotreb.json | Роспотребнадзор оспа обезьян Mpox 2024 | 10 |

---

## GDELT Scout Queries (разведка)

| Кейс | Queries |
|------|---------|
| Красное море | Red Sea shipping crisis Houthi attacks timeline 2023 2024 |
| Boeing | Boeing 737 MAX crisis timeline 2023 2024 door plug incident |
| TikTok | TikTok ban USA regulation crisis 2024 timeline Congress |
| Вагнер | Wagner Group rebellion mutiny Russia June 2023 timeline Prigozhin |
| Яичный кризис | яичный кризис Россия 2024 рост цен яйца дефицит |
| FESCO | FESCO Северилов конфликт корпоративный кризис 2024 |
| Wildberries | Wildberries конфликт корпоративный 2024 Бакальчук |
| OpenAI | OpenAI Sam Altman fired reinstated November 2023 crisis timeline |
| Паралимпиада | Паралимпиада 2024 NPA нейтральный флаг Россия конфликт |
| Mpox | Mpox monkeypox outbreak 2024 WHO emergency timeline |

---

## Итоговая статистика запросов

| Тип | Количество запросов | Результатов |
|-----|---------------------|-------------|
| GDELT Scout | 10 | 150 |
| NewsAPI (международные) | 15 | 150 |
| Russian Media | 10 | 100 |
| **Итого** | **35** | **400** |

После дедупликации: **286 материалов**
