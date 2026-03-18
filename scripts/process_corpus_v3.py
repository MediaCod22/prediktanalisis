#!/usr/bin/env python3
"""
Процессинг собранных медиаматериалов
Версия 3: включает все источники (newsapi, russian, telegram, official)
"""

import json
import os
import hashlib
import csv
from datetime import datetime
from pathlib import Path

# Базовые пути
BASE_DIR = Path("/home/z/my-project/data/raw")
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
    "wb": {"case_id": "wildberries_conflict", "case_name": "Wildberries", "type": "russian"},
    "openai": {"case_id": "openai_altman", "case_name": "OpenAI", "type": "global"},
    "paralympics": {"case_id": "paralympics_npa", "case_name": "Паралимпиада", "type": "russian"},
    "para": {"case_id": "paralympics_npa", "case_name": "Паралимпиада", "type": "russian"},
    "mpox": {"case_id": "mpox_outbreak", "case_name": "Mpox", "type": "global"},
}

# Определение языка по домену
def detect_language(host_name):
    ru_patterns = ['.ru', 'russia', 'russian', 'tass.', 'ria.', 'rbc.', 
                   'kommersant.', 'vedomosti.', 'interfax.', 'forbes.ru',
                   'rg.ru', 'iz.', 'kremlin', 'sledcom', 'government.ru']
    en_patterns = ['.com', '.org', '.gov', '.net', '.int', '.uk', '.eu']
    
    host_lower = host_name.lower()
    
    for pattern in ru_patterns:
        if pattern in host_lower:
            return 'ru'
    return 'en'

# Определение страны источника
def detect_country(host_name):
    country_map = {
        # Российские
        '.ru': 'RU', 'tass.': 'RU', 'ria.': 'RU', 'rbc.': 'RU',
        'kommersant.': 'RU', 'vedomosti.': 'RU', 'interfax.': 'RU',
        'forbes.ru': 'RU', 'rg.ru': 'RU', 'iz.': 'RU', 'kremlin': 'RU',
        'sledcom': 'RU', 'government.ru': 'RU', 'rospotrebnadzor': 'RU',
        'paralymp.ru': 'RU', 'rosstat': 'RU',
        # Международные
        'reuters.com': 'UK', 'theguardian.': 'UK', 'bbc.': 'UK', 'sky.': 'UK',
        'nytimes.': 'US', 'washingtonpost.': 'US', 'cnn.': 'US', 'npr.': 'US',
        'apnews.': 'US', 'abcnews.': 'US', 'fox': 'US', 'cnbc.': 'US',
        'who.int': 'CH', 'aljazeera.': 'QA', 'elpais.': 'ES',
        'euronews.': 'FR', 'france24.': 'FR', 'un.org': 'INT',
        'pentagon': 'US', 'congress.gov': 'US', 'supremecourt': 'US',
        'faa.gov': 'US', 'ntsb.': 'US', 'cdc.gov': 'US',
        'telegram': 'INT', 't.me': 'INT'
    }
    host_lower = host_name.lower()
    for pattern, country in country_map.items():
        if pattern in host_lower:
            return country
    return 'XX'

# Определение блока источника
def detect_source_block(host_name, language, directory_name):
    # Официальные источники
    official_domains = ['who.int', 'cdc.gov', 'faa.gov', 'ntsb.gov', 'un.org', 
                       'kremlin.ru', 'government.ru', 'paralymp.ru', 'rosstat.ru',
                       'rospotrebnadzor.ru', 'sledcom.ru', 'congress.gov', 
                       'supremecourt.gov', 'pentagon']
    host_lower = host_name.lower()
    
    for domain in official_domains:
        if domain in host_lower:
            return 'official'
    
    # Если файл из директории official
    if directory_name == 'official':
        return 'official'
    
    # Телеграм
    if 'telegram' in host_lower or 't.me' in host_lower or directory_name == 'telegram':
        return 'telegram'
    
    # Российские
    if language == 'ru' or '.ru' in host_lower or directory_name == 'russian':
        return 'russian'
    
    return 'international'

# Определение типа источника
def detect_source_type(host_name, source_block):
    host_lower = host_name.lower()
    
    # Telegram каналы
    if source_block == 'telegram':
        return 'telegram_channel'
    
    # Официальные
    if source_block == 'official':
        if 'court' in host_lower or 'суд' in host_lower:
            return 'court'
        if 'gov' in host_lower or 'government' in host_lower:
            return 'government'
        return 'official'
    
    # Новостные агентства
    news_agencies = ['tass', 'ria', 'interfax', 'reuters', 'ap', 'afp', 'tas', 'dpa']
    for agency in news_agencies:
        if agency in host_lower:
            return 'news_agency'
    
    # Газеты
    newspapers = ['kommersant', 'vedomosti', 'nytimes', 'guardian', 'washingtonpost']
    for paper in newspapers:
        if paper in host_lower:
            return 'newspaper'
    
    # ТВ
    tv_channels = ['cnn', 'bbc', 'cnbc', 'abc', 'fox', 'nbc', 'rt.com']
    for tv in tv_channels:
        if tv in host_lower:
            return 'tv'
    
    return 'digital'

# Определение окна сбора
def detect_window(filename):
    if '_year' in filename:
        return 'year'
    elif '_3m' in filename:
        return '3m'
    elif '_1m' in filename:
        return '1m'
    elif '_ext' in filename:
        return 'extended'
    return 'mixed'

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

# Базовая оценка нарративной стадии (эвристика)
def estimate_narrative_stage(title, snippet):
    text = f"{title} {snippet}".lower()
    
    # N5 - развязка/стабилизация
    resolution_keywords = ['resolved', 'stabilized', 'recovery', 'reinstated', 
                          'return', 'agreement', 'settlement', 'peace',
                          'решение', 'стабилизация', 'восстановлен', 'согласие',
                          'снижение цен', 'отмен']
    for kw in resolution_keywords:
        if kw in text:
            return 'N5'
    
    # N4 - системный кризис
    crisis_keywords = ['crisis', 'emergency', 'mutiny', 'rebellion', 
                       'revolt', 'catastrophe', 'collapse', 'war', 'attack',
                       'кризис', 'мятеж', 'бунт', 'катастрофа', 'крах', 'чп',
                       'стрельба', 'арест', 'задержан', 'военный']
    for kw in crisis_keywords:
        if kw in text:
            return 'N4'
    
    # N3 - персонализация
    blame_keywords = ['blame', 'fault', 'responsible', 'guilty', 'accuse',
                      'sue', 'lawsuit', 'charge', 'arrest',
                      'виноват', 'ответственен', 'обвиня', 'иск', 'суд']
    for kw in blame_keywords:
        if kw in text:
            return 'N3'
    
    # N2 - устойчивая проблематизация
    problem_keywords = ['problem', 'issue', 'concern', 'warning', 'risk',
                        'shortage', 'disruption', 'escalation',
                        'проблема', 'проблем', 'риск', 'угроз', 'дефицит',
                        'рост цен', 'подорожан']
    for kw in problem_keywords:
        if kw in text:
            return 'N2'
    
    # N1 - слабая проблематизация
    weak_keywords = ['may', 'could', 'potential', 'possible', 'might',
                     'reported', 'alleged', 'speculation',
                     'может', 'возможн', 'потенциальн', 'сообщается']
    for kw in weak_keywords:
        if kw in text:
            return 'N1'
    
    return 'N0'

# Оценка тональности (эвристика)
def estimate_sentiment(title, snippet):
    text = f"{title} {snippet}".lower()
    
    positive = ['success', 'resolve', 'solution', 'improve', 'growth', 'recovery',
                'успех', 'решение', 'улучш', 'рост', 'восстановл', 'стабилизац',
                'снижение', 'отмена']
    negative = ['crisis', 'crash', 'fail', 'disaster', 'attack', 'war', 'ban',
                'fire', 'kill', 'death', 'arrest', 'criminal', 'scandal',
                'кризис', 'крах', 'провал', 'катастроф', 'атак', 'войн', 'запрет',
                'увольн', 'убийств', 'арест', 'преступл', 'рост цен', 'дефицит',
                'подорожан', 'стрельба', 'мятеж', 'бунт']
    
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
                     'военн', 'войн', 'атак', 'ракет', 'дрон', 'безопасност', 
                     'мятеж', 'security', 'rebellion', 'mutiny'],
        'economic': ['price', 'cost', 'market', 'trade', 'economy', 'inflation',
                     'цен', 'рынок', 'торговл', 'экономик', 'инфляц', 'подорожан',
                     'shipping', 'supply chain'],
        'legal': ['court', 'law', 'sue', 'arrest', 'criminal', 'investigation',
                  'суд', 'закон', 'иск', 'арест', 'преступл', 'следств', 'растрат',
                  'уголовн'],
        'political': ['government', 'president', 'congress', 'parliament', 'policy',
                      'правительств', 'президент', 'конгресс', 'парламент', 'политик',
                      'путин', 'кремл', 'biden', 'trump'],
        'medical': ['health', 'disease', 'virus', 'outbreak', 'vaccine', 'hospital',
                    'здоровь', 'болезн', 'вирус', 'вспышк', 'вакцин', 'больниц',
                    'оспа', 'mpox', 'monkeypox', 'pheic'],
        'managerial': ['ceo', 'board', 'management', 'company', 'corporate',
                       'директор', 'совет', 'управлен', 'компани', 'корпорат',
                       'гендиректор', 'governance'],
        'sport': ['olympic', 'paralympic', 'athlete', 'sport', 'competition',
                  'олимпиад', 'паралимпиад', 'спортсмен', 'спорт', 'соревнован',
                  'ipc', 'npa']
    }
    
    for frame, keywords in frames.items():
        for kw in keywords:
            if kw in text:
                return frame
    
    return 'general'

# Оценка уровня тревожности
def estimate_anxiety_level(title, snippet, narrative_stage):
    if narrative_stage == 'N4':
        return 3
    elif narrative_stage == 'N3':
        return 2
    elif narrative_stage == 'N2':
        return 1
    return 0

# Проверка наличия обвинения
def detect_blame(title, snippet, narrative_stage):
    if narrative_stage in ['N3', 'N4']:
        text = f"{title} {snippet}".lower()
        blame_indicators = ['blame', 'fault', 'responsible', 'guilty', 'accuse',
                           'arrest', 'charge', 'sue', 'criminal',
                           'виноват', 'ответственен', 'обвиня', 'иск', 'суд',
                           'задержан', 'арестован']
        for indicator in blame_indicators:
            if indicator in text:
                return True
    return False

# Проверка системного риска
def detect_systemic_risk(title, snippet, narrative_stage):
    if narrative_stage == 'N4':
        text = f"{title} {snippet}".lower()
        risk_indicators = ['systemic', 'global', 'crisis', 'collapse', 'emergency',
                          'системн', 'глобальн', 'кризис', 'крах', 'чп']
        for indicator in risk_indicators:
            if indicator in text:
                return True
    return False

def process_directory(directory, all_materials, seen_dedup_keys, dir_name='newsapi'):
    """Обрабатывает JSON файлы в указанной директории"""
    
    if not directory.exists():
        return
    
    json_files = list(directory.glob("*.json"))
    
    for json_file in json_files:
        if json_file.name.startswith("scout_"):
            continue
            
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
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
            source_block = detect_source_block(host_name, language, dir_name)
            source_type = detect_source_type(host_name, source_block)
            dedup_key = generate_dedup_key(title, date or 'unknown', host_name)
            
            # Пропускаем дубликаты
            if dedup_key in seen_dedup_keys:
                continue
            seen_dedup_keys.add(dedup_key)
            
            # Оценка нарративных характеристик
            narrative_stage = estimate_narrative_stage(title, snippet)
            sentiment = estimate_sentiment(title, snippet)
            frame_type = estimate_frame(title, snippet)
            anxiety_level = estimate_anxiety_level(title, snippet, narrative_stage)
            blame_present = detect_blame(title, snippet, narrative_stage)
            systemic_risk = detect_systemic_risk(title, snippet, narrative_stage)
            
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
                'source_type': source_type,
                'published_at': date,
                'title': title,
                'url': url,
                'description': snippet[:500] if snippet else '',
                'query_used': query_used,
                'window': window,
                'narrative_stage': narrative_stage,
                'sentiment': sentiment,
                'anxiety_level': anxiety_level,
                'frame_type': frame_type,
                'blame_present': blame_present,
                'systemic_risk': systemic_risk,
                'collected_at': datetime.now().isoformat()
            }
            
            all_materials.append(material)

def main():
    all_materials = []
    seen_dedup_keys = set()
    
    # Обрабатываем все директории
    directories = [
        (BASE_DIR / 'newsapi', 'newsapi'),
        (BASE_DIR / 'russian', 'russian'),
        (BASE_DIR / 'telegram', 'telegram'),
        (BASE_DIR / 'official', 'official'),
    ]
    
    for directory, dir_name in directories:
        print(f"Обработка {dir_name}...")
        process_directory(directory, all_materials, seen_dedup_keys, dir_name)
    
    # Сохраняем в CSV
    if all_materials:
        output_file = PROCESSED_DIR / 'media_corpus_full.csv'
        
        fieldnames = [
            'case_id', 'case_name', 'case_type', 'material_id',
            'source_name', 'source_country', 'source_language', 
            'source_block', 'source_type',
            'published_at', 'title', 'url', 'description',
            'query_used', 'window', 'narrative_stage', 'sentiment',
            'anxiety_level', 'frame_type', 'blame_present', 'systemic_risk',
            'collected_at'
        ]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_materials)
        
        print(f"\n{'='*60}")
        print(f"ИТОГОВАЯ СТАТИСТИКА")
        print(f"{'='*60}")
        print(f"Всего материалов: {len(all_materials)}")
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
        for stg in ['N0', 'N1', 'N2', 'N3', 'N4', 'N5']:
            if stg in stages:
                print(f"  {stg}: {stages[stg]}")
        
        # Статистика по фреймам
        frames = {}
        for m in all_materials:
            frm = m['frame_type']
            if frm not in frames:
                frames[frm] = 0
            frames[frm] += 1
        
        print("\nПо фреймам:")
        for frm, count in sorted(frames.items()):
            print(f"  {frm}: {count}")

if __name__ == '__main__':
    main()
