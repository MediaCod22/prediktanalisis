#!/usr/bin/env python3
"""
Процессинг собранных медиаматериалов
Объединение, дедупликация, базовая разметка
Версия 2: включает российские источники
"""

import json
import os
import hashlib
import csv
from datetime import datetime
from pathlib import Path

# Базовые пути
RAW_DIR = Path("/home/z/my-project/data/raw/newsapi")
RAW_RU_DIR = Path("/home/z/my-project/data/raw/russian")
PROCESSED_DIR = Path("/home/z/my-project/data/processed")

# Маппинг кейсов
CASE_MAPPING = {
    "redsea": {"case_id": "redsea_shipping", "case_name": "Красное море", "type": "global"},
    "boeing": {"case_id": "boeing_crisis", "case_name": "Boeing", "type": "global"},
    "tiktok": {"case_id": "tiktok_regulatory", "case_name": "TikTok", "type": "global"},
    "wagner": {"case_id": "wagner_mutiny", "case_name": "ЧВК Вагнер", "type": "russian"},
    "eggs": {"case_id": "egg_crisis_russia", "case_name": "Яичный кризис", "type": "russian"},
    "fesco": {"case_id": "fesco_severilov", "case_name": "FESCO", "type": "russian"},
    "wildberries": {"case_id": "wildberries_conflict", "case_name": "Wildberries", "type": "russian"},
    "openai": {"case_id": "openai_altman", "case_name": "OpenAI", "type": "global"},
    "paralympics": {"case_id": "paralympics_npa", "case_name": "Паралимпиада", "type": "russian"},
    "mpox": {"case_id": "mpox_outbreak", "case_name": "Mpox", "type": "global"},
}

# Определение языка по домену
def detect_language(host_name):
    ru_domains = ['.ru', 'russia', 'russian', 'tass.ru', 'ria.ru', 'rbc.ru', 
                  'kommersant.ru', 'vedomosti.ru', 'interfax.ru', 'forbes.ru',
                  'rg.ru', 'championat.com', 'matchtv', 'rosstat', 'rospotrebnadzor',
                  'paralymp.ru']
    host_lower = host_name.lower()
    for domain in ru_domains:
        if domain in host_lower:
            return 'ru'
    return 'en'

# Определение страны источника
def detect_country(host_name):
    country_map = {
        '.ru': 'RU', 'tass.': 'RU', 'ria.': 'RU', 'rbc.': 'RU',
        'kommersant.': 'RU', 'vedomosti.': 'RU', 'interfax.': 'RU',
        'forbes.ru': 'RU', 'rg.ru': 'RU', 'rosstat': 'RU', 'rospotrebnadzor': 'RU',
        'paralymp.ru': 'RU',
        'reuters.com': 'UK', 'theguardian.': 'UK', 'bbc.': 'UK', 'sky.': 'UK',
        'nytimes.': 'US', 'washingtonpost.': 'US', 'cnn.': 'US', 'npr.': 'US',
        'apnews.': 'US', 'abcnews.': 'US', 'fox': 'US', 'cnbc.': 'US',
        'who.int': 'CH', 'aljazeera.': 'QA', 'elpais.': 'ES',
        'euronews.': 'FR', 'france24.': 'FR'
    }
    host_lower = host_name.lower()
    for pattern, country in country_map.items():
        if pattern in host_lower:
            return country
    return 'XX'

# Определение блока источника
def detect_source_block(host_name, language):
    official_domains = ['who.int', 'cdc.gov', 'faa.gov', 'ntsb.gov', 'un.org', 
                       'kremlin.ru', 'government.ru', 'paralymp.ru', 'rosstat.ru',
                       'rospotrebnadzor.ru']
    host_lower = host_name.lower()
    
    for domain in official_domains:
        if domain in host_lower:
            return 'official'
    
    if language == 'ru' or '.ru' in host_lower:
        return 'russian'
    
    return 'international'

# Определение окна сбора
def detect_window(filename):
    if '_year_' in filename:
        return 'year'
    elif '_3m_' in filename:
        return '3m'
    elif '_1m_' in filename:
        return '1m'
    elif '_ru_' in filename or '_rbc' in filename or '_tass' in filename or '_interfax' in filename or '_kommersant' in filename or '_vedomosti' in filename or '_rosstat' in filename or '_pcr' in filename or '_rospotreb' in filename:
        return 'russian_sources'
    return 'unknown'

# Генерация ключа дедупликации
def generate_dedup_key(title, date, source):
    combined = f"{title}|{date}|{source}"
    return hashlib.md5(combined.encode()).hexdigest()[:16]

# Извлечение кейса из имени файла
def extract_case_from_filename(filename):
    for key in CASE_MAPPING.keys():
        if key in filename.lower():
            return key
    return None

# Базовая оценка нарративной стадии нарратива (эвристика)
def estimate_narrative_stage(title, snippet):
    text = f"{title} {snippet}".lower()
    
    # N4 - системный кризис
    crisis_keywords = ['crisis', 'emergency', 'mutiny', 'rebellion', 
                       'revolt', 'catastrophe', 'collapse', 'war',
                       'кризис', 'мятеж', 'бунт', 'катастрофа', 'крах', 'чп']
    for kw in crisis_keywords:
        if kw in text:
            return 'N4'
    
    # N3 - персонализация
    blame_keywords = ['blame', 'fault', 'responsible', 'guilty', 'accuse',
                      'виноват', 'ответственен', 'обвиня', 'задержан', 'арестован']
    for kw in blame_keywords:
        if kw in text:
            return 'N3'
    
    # N2 - устойчивая проблематизация
    problem_keywords = ['problem', 'issue', 'concern', 'warning', 'risk',
                        'проблема', 'проблем', 'риск', 'угроз', 'дефицит']
    for kw in problem_keywords:
        if kw in text:
            return 'N2'
    
    # N1 - слабая проблематизация
    weak_keywords = ['may', 'could', 'potential', 'possible', 'might',
                     'может', 'возможн', 'потенциальн']
    for kw in weak_keywords:
        if kw in text:
            return 'N1'
    
    return 'N0'

# Оценка тональности (эвристика)
def estimate_sentiment(title, snippet):
    text = f"{title} {snippet}".lower()
    
    positive = ['success', 'resolve', 'solution', 'improve', 'growth', 'recovery',
                'успех', 'решение', 'улучш', 'рост', 'восстановл', 'стабилизац']
    negative = ['crisis', 'crash', 'fail', 'disaster', 'attack', 'war', 'ban',
                'fire', 'kill', 'death', 'arrest', 'criminal',
                'кризис', 'крах', 'провал', 'катастроф', 'атак', 'войн', 'запрет',
                'увольн', 'убийств', 'арест', 'преступл', 'рост цен', 'дефицит']
    
    pos_count = sum(1 for kw in positive if kw in text)
    neg_count = sum(1 for kw in negative if kw in text)
    
    if neg_count > pos_count:
        return 'negative'
    elif pos_count > neg_count:
        return 'positive'
    elif neg_count > 0 and pos_count > 0:
        return 'mixed'
    return 'neutral'

# Определение фрейма (эвристика)
def estimate_frame(title, snippet):
    text = f"{title} {snippet}".lower()
    
    frames = {
        'security': ['military', 'war', 'attack', 'missile', 'drone', 'security',
                     'военн', 'войн', 'атак', 'ракет', 'дрон', 'безопасност', 'мятеж'],
        'economic': ['price', 'cost', 'market', 'trade', 'economy', 'inflation',
                     'цен', 'рынок', 'торговл', 'экономик', 'инфляц', 'подорожан'],
        'legal': ['court', 'law', 'sue', 'arrest', 'criminal', 'investigation',
                  'суд', 'закон', 'иск', 'арест', 'преступл', 'следств', 'растрат'],
        'political': ['government', 'president', 'congress', 'parliament', 'policy',
                      'правительств', 'президент', 'конгресс', 'парламент', 'политик',
                      'путин', 'кремл'],
        'medical': ['health', 'disease', 'virus', 'outbreak', 'vaccine', 'hospital',
                    'здоровь', 'болезн', 'вирус', 'вспышк', 'вакцин', 'больниц',
                    'оспа', 'mpox'],
        'managerial': ['ceo', 'board', 'management', 'company', 'corporate',
                       'директор', 'совет', 'управлен', 'компани', 'корпорат',
                       'гендиректор'],
        'sport': ['olympic', 'paralympic', 'athlete', 'sport', 'competition',
                  'олимпиад', 'паралимпиад', 'спортсмен', 'спорт', 'соревнован',
                  'ipc', 'mpa']
    }
    
    for frame, keywords in frames.items():
        for kw in keywords:
            if kw in text:
                return frame
    
    return 'general'

def process_directory(directory, all_materials, seen_dedup_keys, source_type='newsapi'):
    """Обрабатывает JSON файлы в указанной директории"""
    
    json_files = list(directory.glob("*.json"))
    
    for json_file in json_files:
        if json_file.name.startswith("scout_"):
            continue
            
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Ошибка чтения {json_file}: {e}")
            continue
        
        case_key = extract_case_from_filename(json_file.name)
        if not case_key:
            continue
        
        case_info = CASE_MAPPING[case_key]
        query_used = json_file.stem
        window = detect_window(json_file.name)
        
        for item in data:
            title = item.get('name', '')
            snippet = item.get('snippet', '')
            url = item.get('url', '')
            host_name = item.get('host_name', '')
            date = item.get('date', '')
            
            if not title:
                continue
            
            # Определяем атрибуты
            language = detect_language(host_name)
            country = detect_country(host_name)
            source_block = detect_source_block(host_name, language)
            dedup_key = generate_dedup_key(title, date or 'unknown', host_name)
            
            # Пропускаем дубликаты
            if dedup_key in seen_dedup_keys:
                continue
            seen_dedup_keys.add(dedup_key)
            
            # Создаём запись
            material = {
                'case_id': case_info['case_id'],
                'case_name': case_info['case_name'],
                'case_type': case_info['type'],
                'material_id': dedup_key,
                'source_name': host_name,
                'source_country': country,
                'source_language': language,
                'source_block': source_block,
                'published_at': date,
                'title': title,
                'url': url,
                'description': snippet[:500] if snippet else '',
                'query_used': query_used,
                'window': window,
                'narrative_stage': estimate_narrative_stage(title, snippet),
                'sentiment': estimate_sentiment(title, snippet),
                'frame_type': estimate_frame(title, snippet),
                'collected_at': datetime.now().isoformat()
            }
            
            all_materials.append(material)

def main():
    all_materials = []
    seen_dedup_keys = set()
    
    # Обрабатываем оба каталога
    print("Обработка NewsAPI...")
    process_directory(RAW_DIR, all_materials, seen_dedup_keys, 'newsapi')
    
    print("Обработка российских источников...")
    process_directory(RAW_RU_DIR, all_materials, seen_dedup_keys, 'russian')
    
    # Сохраняем в CSV
    if all_materials:
        output_file = PROCESSED_DIR / 'media_corpus_raw.csv'
        
        fieldnames = [
            'case_id', 'case_name', 'case_type', 'material_id',
            'source_name', 'source_country', 'source_language', 'source_block',
            'published_at', 'title', 'url', 'description',
            'query_used', 'window', 'narrative_stage', 'sentiment', 'frame_type',
            'collected_at'
        ]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_materials)
        
        print(f"\nОбработано материалов: {len(all_materials)}")
        print(f"Сохранено в: {output_file}")
        
        # Статистика по кейсам
        cases = {}
        for m in all_materials:
            cid = m['case_id']
            if cid not in cases:
                cases[cid] = 0
            cases[cid] += 1
        
        print("\nПо кейсам:")
        for cid, count in sorted(cases.items()):
            print(f"  {cid}: {count}")
        
        # Статистика по блокам
        blocks = {}
        for m in all_materials:
            blk = m['source_block']
            if blk not in blocks:
                blocks[blk] = 0
            blocks[blk] += 1
        
        print("\nПо блокам источников:")
        for blk, count in sorted(blocks.items()):
            print(f"  {blk}: {count} ({count*100/len(all_materials):.1f}%)")
        
        # Статистика по нарративным стадиям
        stages = {}
        for m in all_materials:
            stg = m['narrative_stage']
            if stg not in stages:
                stages[stg] = 0
            stages[stg] += 1
        
        print("\nПо нарративным стадиям:")
        for stg, count in sorted(stages.items()):
            print(f"  {stg}: {count}")

if __name__ == '__main__':
    main()
