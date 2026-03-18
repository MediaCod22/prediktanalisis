#!/usr/bin/env python3
"""
Обработка новых кейсов: Nord Stream и Nornickel
Объединение материалов в CSV с коэффициентами анализа
"""

import json
import csv
import os
import hashlib
from datetime import datetime
from pathlib import Path

# Базовые пути
BASE_DIR = Path("/home/z/my-project")
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

# Новые кейсы
NEW_CASES = ["nord_stream", "nornickel"]

# Коэффициенты для оценки источников
SOURCE_TYPE_SCALE = {
    # Официальные источники = 1.0
    "kremlin.ru": 1.0, "government.ru": 1.0, "whitehouse.gov": 1.0,
    "un.org": 1.0, "europa.eu": 1.0, "bundestag.de": 1.0,
    "government.se": 1.0, "stm.dk": 1.0, "rpn.gov.ru": 1.0,
    "sledcom.ru": 1.0, "genproc.gov.ru": 1.0, "who.int": 1.0,
    # Крупные международные агентства = 0.8
    "reuters.com": 0.8, "apnews.com": 0.8, "bbc.com": 0.8,
    "bloomberg.com": 0.8, "ft.com": 0.8, "wsj.com": 0.8,
    "nytimes.com": 0.8, "washingtonpost.com": 0.8, "theguardian.com": 0.8,
    # Российские государственные = 0.7
    "tass.ru": 0.7, "ria.ru": 0.7, "rbc.ru": 0.7, "rt.com": 0.7,
    # Бизнес-издания = 0.75
    "kommersant.ru": 0.75, "vedomosti.ru": 0.75, "forbes.ru": 0.75,
    # Прочие = 0.5
    "default": 0.5
}

# Тональность по ключевым словам
TONE_KEYWORDS = {
    "critical": ["критика", "критикует", "скандал", "виноват", "ошибка", "провал",
                 "criticism", "scandal", "blame", "failure", "fault", "negligence",
                 "халатность", "бездействие", "негативно", "резко", "осуждение"],
    "positive": ["успех", "решение", "договорились", "компенсация", "сотрудничество",
                 "success", "agreement", "compensation", "cooperation", "решена",
                 "благодарность", "хорошо"],
    "informational": ["сообщает", "заявил", "по данным", "источник", "расследование",
                      "reports", "according to", "investigation", "statement"]
}

def get_source_type_scale(url):
    """Определение коэффициента типа источника"""
    if not url:
        return 0.5
    url_lower = url.lower()
    for domain, scale in SOURCE_TYPE_SCALE.items():
        if domain in url_lower:
            return scale
    return SOURCE_TYPE_SCALE["default"]

def analyze_tone(text):
    """Анализ тональности текста"""
    if not text:
        return "neutral"
    text_lower = text.lower()

    critical_count = sum(1 for kw in TONE_KEYWORDS["critical"] if kw in text_lower)
    positive_count = sum(1 for kw in TONE_KEYWORDS["positive"] if kw in text_lower)
    info_count = sum(1 for kw in TONE_KEYWORDS["informational"] if kw in text_lower)

    if critical_count > positive_count and critical_count > info_count:
        return "critical"
    elif positive_count > critical_count and positive_count > info_count:
        return "positive"
    elif info_count >= critical_count and info_count >= positive_count:
        return "informational"
    return "neutral"

def detect_forecast(text):
    """Обнаружение прогнозов в тексте"""
    if not text:
        return {"has_forecast": False, "forecast_type": None, "detail_level": None}

    text_lower = text.lower()
    forecast_keywords = {
        "positive": ["ожидается рост", "прогнозируется улучшение", "будет решено",
                     "expected to improve", "forecast growth", "will be resolved"],
        "negative": ["ожидается ухудшение", "может привести", "риск",
                     "may lead to", "risk of", "could worsen", "угроза"]
    }

    detail_keywords = {
        "specific": ["конкретно", "в течение", "к дате", "в сумме", "цифры",
                     "specifically", "within", "by date", "amount", "figures"],
        "general": ["в целом", "в перспективе", "возможно", "в будущем",
                    "in general", "in perspective", "possibly", "in the future"]
    }

    has_positive = any(kw in text_lower for kw in forecast_keywords["positive"])
    has_negative = any(kw in text_lower for kw in forecast_keywords["negative"])

    if has_positive or has_negative:
        forecast_type = "positive" if has_positive else "negative"
        detail = "specific" if any(kw in text_lower for kw in detail_keywords["specific"]) else "general"
        return {"has_forecast": True, "forecast_type": forecast_type, "detail_level": detail}

    return {"has_forecast": False, "forecast_type": None, "detail_level": None}

def parse_date(date_str):
    """Парсинг даты в различных форматах"""
    if not date_str:
        return "unknown"

    formats = [
        "%Y-%m-%d", "%d.%m.%Y", "%Y/%m/%d",
        "%B %d, %Y", "%d %B %Y", "%Y-%m",
        "%Y"
    ]

    for fmt in formats:
        try:
            parsed = datetime.strptime(date_str.strip(), fmt)
            return parsed.strftime("%Y-%m-%d")
        except:
            continue

    # Если год указан как диапазон
    if "2022-2024" in date_str or "2020-2021" in date_str:
        return date_str

    return "unknown"

def create_hash(title, date, source):
    """Создание уникального хеша для дедупликации"""
    combined = f"{title}|{date}|{source}"
    return hashlib.md5(combined.encode()).hexdigest()[:12]

def process_case(case_name):
    """Обработка одного кейса"""
    materials = []
    case_dir = RAW_DIR / case_name

    # Читаем scout файл
    scout_file = case_dir / "scout" / f"scout_{case_name}.json"
    if scout_file.exists():
        with open(scout_file, 'r', encoding='utf-8') as f:
            scout_data = json.load(f)

    # Обрабатываем материалы из international
    int_dir = case_dir / "international"
    if int_dir.exists():
        for json_file in int_dir.glob("*.json"):
            if json_file.name.startswith("_") or json_file.name.startswith("COLLECTION"):
                continue
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                text = f"{data.get('title', '')} {data.get('snippet', '')}"
                forecast_info = detect_forecast(text)

                material = {
                    "id": data.get("id", json_file.stem),
                    "case_id": case_name,
                    "title": data.get("title", ""),
                    "source": data.get("source", ""),
                    "url": data.get("url", ""),
                    "date": parse_date(data.get("date", "")),
                    "snippet": data.get("snippet", "")[:500] if data.get("snippet") else "",
                    "block": "international",
                    "narrative_stage": data.get("narrative_stage", "N2"),
                    "source_type_scale": get_source_type_scale(data.get("url", "")),
                    "article_tone": analyze_tone(text),
                    "situation_presentation": "neutral",  # Будет определено позже
                    "forecast_presence": forecast_info["has_forecast"],
                    "forecast_type": forecast_info["forecast_type"] or "",
                    "forecast_detail_level": forecast_info["detail_level"] or "",
                    "hash": create_hash(data.get("title", ""), data.get("date", ""), data.get("source", ""))
                }
                materials.append(material)
            except Exception as e:
                print(f"Error processing {json_file}: {e}")

    # Обрабатываем материалы из russian
    ru_dir = case_dir / "russian"
    if ru_dir.exists():
        for json_file in ru_dir.glob("*.json"):
            if json_file.name.startswith("_") or json_file.name.startswith("COLLECTION"):
                continue
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                text = f"{data.get('title', '')} {data.get('snippet', '')}"
                forecast_info = detect_forecast(text)

                material = {
                    "id": data.get("id", json_file.stem),
                    "case_id": case_name,
                    "title": data.get("title", ""),
                    "source": data.get("source", ""),
                    "url": data.get("url", ""),
                    "date": parse_date(data.get("date", "")),
                    "snippet": data.get("snippet", "")[:500] if data.get("snippet") else "",
                    "block": "russian",
                    "narrative_stage": data.get("narrative_stage", "N2"),
                    "source_type_scale": get_source_type_scale(data.get("url", "")),
                    "article_tone": analyze_tone(text),
                    "situation_presentation": "neutral",
                    "forecast_presence": forecast_info["has_forecast"],
                    "forecast_type": forecast_info["forecast_type"] or "",
                    "forecast_detail_level": forecast_info["detail_level"] or "",
                    "hash": create_hash(data.get("title", ""), data.get("date", ""), data.get("source", ""))
                }
                materials.append(material)
            except Exception as e:
                print(f"Error processing {json_file}: {e}")

    return materials

def main():
    """Главная функция"""
    all_materials = []

    for case in NEW_CASES:
        print(f"Processing case: {case}")
        materials = process_case(case)
        print(f"  Collected {len(materials)} materials")
        all_materials.extend(materials)

    # Дедупликация по хешу
    seen_hashes = set()
    unique_materials = []
    for m in all_materials:
        if m["hash"] not in seen_hashes:
            seen_hashes.add(m["hash"])
            unique_materials.append(m)

    print(f"\nTotal unique materials: {len(unique_materials)}")

    # Сохраняем в CSV
    output_file = PROCESSED_DIR / "new_cases_corpus.csv"

    fieldnames = [
        "id", "case_id", "title", "source", "url", "date", "snippet",
        "block", "narrative_stage", "source_type_scale", "article_tone",
        "situation_presentation", "forecast_presence", "forecast_type",
        "forecast_detail_level", "hash"
    ]

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique_materials)

    print(f"Saved to: {output_file}")

    # Статистика
    print("\n=== Statistics ===")
    for case in NEW_CASES:
        case_materials = [m for m in unique_materials if m["case_id"] == case]
        print(f"\n{case}:")
        print(f"  Total: {len(case_materials)}")
        blocks = {}
        stages = {}
        tones = {}
        for m in case_materials:
            blocks[m["block"]] = blocks.get(m["block"], 0) + 1
            stages[m["narrative_stage"]] = stages.get(m["narrative_stage"], 0) + 1
            tones[m["article_tone"]] = tones.get(m["article_tone"], 0) + 1
        print(f"  By block: {blocks}")
        print(f"  By stage: {stages}")
        print(f"  By tone: {tones}")

if __name__ == "__main__":
    main()
