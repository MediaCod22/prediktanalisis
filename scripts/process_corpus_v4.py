#!/usr/bin/env python3
"""
Расширенная аннотация корпуса с новыми коэффициентами
Версия 4: добавлены предиктивные индикаторы
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

# ============================================
# НОВЫЕ КОЭФФИЦИЕНТЫ
# ============================================

def get_source_officiality_score(host_name, source_block):
    """
    Шкала официальности источника (0-5)
    0 = блог/соцсеть
    1 = альтернативное СМИ
    2 = независимое СМИ
    3 = мейнстрим СМИ
    4 = государственное СМИ
    5 = официальный орган
    """
    host_lower = host_name.lower()
    
    # Официальные органы (5)
    official_max = ['who.int', 'cdc.gov', 'faa.gov', 'ntsb.gov', 'un.org',
                   'kremlin.ru', 'government.ru', 'sledcom.ru', 'paralymp.ru',
                   'congress.gov', 'supremecourt.gov', 'ipc.org']
    for domain in official_max:
        if domain in host_lower:
            return 5
    
    # Государственные СМИ (4)
    state_media = ['tass.', 'ria.', 'rg.ru', 'rt.com']
    for domain in state_media:
        if domain in host_lower:
            return 4
    
    # Мейнстрим СМИ (3)
    mainstream = ['reuters.com', 'apnews.', 'bbc.', 'cnn.', 'nytimes.',
                  'theguardian.', 'rbc.ru', 'interfax.', 'kommersant.',
                  'vedomosti.', 'forbes.ru', 'aljazeera.']
    for domain in mainstream:
        if domain in host_lower:
            return 3
    
    # Независимые/деловые СМИ (2)
    independent = ['meduza', 'novaya', 'dw.com', 'rfi.fr', 'bbc.com',
                   'themoscowtimes', 'axios.', 'npr.']
    for domain in independent:
        if domain in host_lower:
            return 2
    
    # Telegram/блоги (0-1)
    if 'telegram' in host_lower or source_block == 'telegram':
        return 1
    
    # По умолчанию
    return 2


def get_article_tone(title, snippet):
    """
    Общий тон статьи: critical/informational/positive/analytical/emotional
    """
    text = f"{title} {snippet}".lower()
    
    # Критический тон
    critical_words = ['fail', 'crisis', 'collapse', 'disaster', 'scandal', 'betrayal',
                      'провал', 'кризис', 'крах', 'катастрофа', 'скандал', 'предательств']
    critical_count = sum(1 for w in critical_words if w in text)
    
    # Эмоциональный тон
    emotional_words = ['shocking', 'terrifying', 'dramatic', 'unprecedented', 'explosive',
                       'шок', 'ужас', 'драма', 'беспрецедентн', 'взрывн']
    emotional_count = sum(1 for w in emotional_words if w in text)
    
    # Позитивный тон
    positive_words = ['success', 'breakthrough', 'resolve', 'improvement', 'recovery',
                      'успех', 'прорыв', 'решение', 'улучшен', 'восстановлен']
    positive_count = sum(1 for w in positive_words if w in text)
    
    # Аналитический тон
    analytical_words = ['analysis', 'report', 'study', 'data', 'experts say', 'according to',
                        'анализ', 'отчёт', 'исследован', 'данные', 'эксперты', 'согласно']
    analytical_count = sum(1 for w in analytical_words if w in text)
    
    # Определение доминирующего тона
    scores = {
        'critical': critical_count,
        'emotional': emotional_count,
        'positive': positive_count,
        'analytical': analytical_count
    }
    
    max_score = max(scores.values())
    if max_score == 0:
        return 'informational'
    
    return max(scores, key=scores.get)


def get_situation_framing(title, snippet):
    """
    Подача исследуемой ситуации: critical/informational/positive/neutral/conflicting
    """
    text = f"{title} {snippet}".lower()
    
    # Критическая подача
    if any(w in text for w in ['crisis', 'emergency', 'threat', 'danger', 'collapse',
                                'кризис', 'чп', 'угроза', 'опасн', 'крах']):
        return 'critical'
    
    # Конфликтная подача
    if any(w in text for w in ['conflict', 'dispute', 'clash', 'confrontation',
                                'конфликт', 'спор', 'столкновен', 'противостоян']):
        return 'conflicting'
    
    # Позитивная подача
    if any(w in text for w in ['solution', 'agreement', 'progress', 'improvement',
                                'решение', 'согласие', 'прогресс', 'улучшен']):
        return 'positive'
    
    # Нейтральная подача (факты без оценки)
    if any(w in text for w in ['reported', 'announced', 'stated', 'according',
                                'сообща', 'объяви', 'заяви', 'согласно']):
        return 'neutral'
    
    return 'informational'


def get_forecast_presence(title, snippet):
    """
    Есть ли прогноз и какой: negative_forecast/positive_forecast/neutral_forecast/no_forecast
    """
    text = f"{title} {snippet}".lower()
    
    # Индикаторы прогноза
    forecast_indicators = ['will', 'may', 'could', 'expect', 'predict', 'forecast', 'projected',
                          'будет', 'может', 'ожидается', 'прогноз', 'предсказа']
    
    has_forecast = any(w in text for w in forecast_indicators)
    
    if not has_forecast:
        return 'no_forecast'
    
    # Негативный прогноз
    if any(w in text for w in ['worsen', 'decline', 'collapse', 'escalate', 'crash',
                              'ухудш', 'снижени', 'крах', 'эскалаци', 'паден']):
        return 'negative_forecast'
    
    # Позитивный прогноз
    if any(w in text for w in ['improve', 'recover', 'resolve', 'growth', 'stabilize',
                              'улучш', 'восстанов', 'решение', 'рост', 'стабилиза']):
        return 'positive_forecast'
    
    return 'neutral_forecast'


def get_forecast_detail_level(title, snippet):
    """
    Степень детализации прогноза: specific/general/none
    """
    text = f"{title} {snippet}".lower()
    
    # Прогноза нет
    if get_forecast_presence(title, snippet) == 'no_forecast':
        return 'none'
    
    # Конкретный прогноз (цифры, даты, имена)
    import re
    has_numbers = bool(re.search(r'\d+%|\d+ percent|\d+ процен', text))
    has_dates = bool(re.search(r'202[0-9]|в [а-я]+|in [a-z]+|by [a-z]+', text))
    has_specifics = any(w in text for w in ['specifically', 'exactly', 'precisely',
                                             'конкретно', 'точно', 'именно'])
    
    if has_numbers or has_dates or has_specifics:
        return 'specific'
    
    return 'general'


def get_anxiety_level(title, snippet, narrative_stage):
    """
    Уровень тревожности материала: 0-3
    """
    text = f"{title} {snippet}".lower()
    
    # Базовый уровень от стадии
    stage_anxiety = {
        'N0': 0, 'N1': 1, 'N2': 1, 'N3': 2, 'N4': 3, 'N5': 0
    }
    base = stage_anxiety.get(narrative_stage, 0)
    
    # Модификаторы
    high_anxiety_words = ['panic', 'fear', 'terrify', 'danger', 'threat', 'emergency',
                          'паник', 'страх', 'ужас', 'опасн', 'угроза', 'чп']
    if any(w in text for w in high_anxiety_words):
        base = min(3, base + 1)
    
    return base


def get_predictive_signal(title, snippet, narrative_stage, forecast):
    """
    Есть ли предиктивный сигнал: early_warning/escalation_signal/peak_signal/resolution_signal/none
    """
    text = f"{title} {snippet}".lower()
    
    # Ранний сигнал (N1-N2)
    if narrative_stage in ['N1', 'N2']:
        early_words = ['may', 'could', 'potential', 'risk', 'concern',
                       'может', 'возможн', 'риск', 'беспокойств']
        if any(w in text for w in early_words):
            return 'early_warning'
    
    # Сигнал эскалации (N2-N3)
    if narrative_stage in ['N2', 'N3']:
        escalation_words = ['escalate', 'worsen', 'intensify', 'grow',
                           'эскалаци', 'ухудш', 'нараста', 'усилива']
        if any(w in text for w in escalation_words):
            return 'escalation_signal'
    
    # Пиковый сигнал (N4)
    if narrative_stage == 'N4':
        return 'peak_signal'
    
    # Сигнал развязки (N5)
    if narrative_stage == 'N5':
        return 'resolution_signal'
    
    return 'none'


# ============================================
# БАЗОВЫЕ ФУНКЦИИ (из v3)
# ============================================

def detect_language(host_name):
    ru_patterns = ['.ru', 'russia', 'russian', 'tass.', 'ria.', 'rbc.', 
                   'kommersant.', 'vedomosti.', 'interfax.', 'forbes.ru',
                   'rg.ru', 'iz.', 'kremlin', 'sledcom', 'government.ru']
    host_lower = host_name.lower()
    for pattern in ru_patterns:
        if pattern in host_lower:
            return 'ru'
    return 'en'

def detect_country(host_name):
    country_map = {
        '.ru': 'RU', 'tass.': 'RU', 'ria.': 'RU', 'rbc.': 'RU',
        'kommersant.': 'RU', 'vedomosti.': 'RU', 'interfax.': 'RU',
        'forbes.ru': 'RU', 'rg.ru': 'RU', 'iz.': 'RU', 'kremlin': 'RU',
        'reuters.com': 'UK', 'theguardian.': 'UK', 'bbc.': 'UK',
        'nytimes.': 'US', 'cnn.': 'US', 'apnews.': 'US',
        'who.int': 'CH', 'aljazeera.': 'QA', 'un.org': 'INT',
        'congress.gov': 'US', 'supremecourt': 'US',
    }
    host_lower = host_name.lower()
    for pattern, country in country_map.items():
        if pattern in host_lower:
            return country
    return 'XX'

def detect_source_block(host_name, language, directory_name):
    official_domains = ['who.int', 'cdc.gov', 'faa.gov', 'ntsb.gov', 'un.org', 
                       'kremlin.ru', 'government.ru', 'paralymp.ru',
                       'congress.gov', 'supremecourt.gov']
    host_lower = host_name.lower()
    for domain in official_domains:
        if domain in host_lower:
            return 'official'
    if directory_name == 'official':
        return 'official'
    if 'telegram' in host_lower or directory_name == 'telegram':
        return 'telegram'
    if language == 'ru' or '.ru' in host_lower or directory_name == 'russian':
        return 'russian'
    return 'international'

def detect_source_type(host_name, source_block):
    host_lower = host_name.lower()
    if source_block == 'telegram':
        return 'telegram_channel'
    if source_block == 'official':
        if 'court' in host_lower:
            return 'court'
        return 'government'
    news_agencies = ['tass', 'ria', 'interfax', 'reuters', 'ap', 'afp']
    for agency in news_agencies:
        if agency in host_lower:
            return 'news_agency'
    newspapers = ['kommersant', 'vedomosti', 'nytimes', 'guardian']
    for paper in newspapers:
        if paper in host_lower:
            return 'newspaper'
    return 'digital'

def detect_window(filename):
    if '_year' in filename:
        return 'year'
    elif '_3m' in filename:
        return '3m'
    elif '_1m' in filename:
        return '1m'
    elif '_ext' in filename or '_mass' in filename:
        return 'extended'
    return 'mixed'

def generate_dedup_key(title, date, source):
    combined = f"{title}|{date}|{source}"
    return hashlib.md5(combined.encode()).hexdigest()[:16]

def extract_case_from_filename(filename):
    for key in CASE_MAPPING.keys():
        if key in filename.lower():
            return key
    return None

def estimate_narrative_stage(title, snippet):
    text = f"{title} {snippet}".lower()
    if any(kw in text for kw in ['resolved', 'reinstated', 'решение', 'стабилизац', 'отмен']):
        return 'N5'
    if any(kw in text for kw in ['crisis', 'emergency', 'mutiny', 'rebellion', 'attack',
                                  'кризис', 'мятеж', 'бунт', 'катастрофа', 'стрельба', 'арест']):
        return 'N4'
    if any(kw in text for kw in ['blame', 'fault', 'accuse', 'sue', 'arrest',
                                  'виноват', 'обвиня', 'иск', 'суд']):
        return 'N3'
    if any(kw in text for kw in ['problem', 'risk', 'shortage', 'дефицит', 'рост цен']):
        return 'N2'
    if any(kw in text for kw in ['may', 'could', 'potential', 'может', 'возможн']):
        return 'N1'
    return 'N0'

def estimate_sentiment(title, snippet):
    text = f"{title} {snippet}".lower()
    positive = ['success', 'resolve', 'recovery', 'успех', 'решение', 'снижение']
    negative = ['crisis', 'fail', 'disaster', 'attack', 'crash', 'рост цен',
                'кризис', 'провал', 'катастроф', 'дефицит', 'подорожан']
    pos_count = sum(1 for kw in positive if kw in text)
    neg_count = sum(1 for kw in negative if kw in text)
    if neg_count > pos_count:
        return 'negative'
    elif pos_count > neg_count:
        return 'positive'
    return 'neutral'

def estimate_frame(title, snippet):
    text = f"{title} {snippet}".lower()
    frames = {
        'security': ['military', 'war', 'attack', 'missile', 'security',
                     'военн', 'войн', 'атак', 'мятеж'],
        'economic': ['price', 'cost', 'market', 'inflation',
                     'цен', 'рынок', 'экономик', 'подорожан'],
        'legal': ['court', 'law', 'sue', 'arrest', 'criminal',
                  'суд', 'закон', 'иск', 'преступл', 'растрат'],
        'political': ['government', 'president', 'congress', 'policy',
                      'правительств', 'президент', 'политик'],
        'medical': ['health', 'disease', 'virus', 'vaccine',
                    'здоровь', 'болезн', 'вирус', 'вспышк'],
        'managerial': ['ceo', 'board', 'management', 'company',
                       'директор', 'совет', 'управлен', 'компани'],
        'sport': ['olympic', 'paralympic', 'athlete', 'sport',
                  'олимпиад', 'паралимпиад', 'спорт', 'соревнован']
    }
    for frame, keywords in frames.items():
        for kw in keywords:
            if kw in text:
                return frame
    return 'general'

def detect_blame(title, snippet, narrative_stage):
    if narrative_stage in ['N3', 'N4']:
        text = f"{title} {snippet}".lower()
        if any(w in text for w in ['blame', 'fault', 'responsible', 'arrest',
                                   'виноват', 'ответствен', 'обвиня', 'суд']):
            return True
    return False

def detect_systemic_risk(title, snippet, narrative_stage):
    if narrative_stage == 'N4':
        text = f"{title} {snippet}".lower()
        if any(w in text for w in ['systemic', 'global', 'collapse',
                                   'системн', 'глобальн', 'крах']):
            return True
    return False

def process_directory(directory, all_materials, seen_dedup_keys, dir_name='newsapi'):
    if not directory.exists():
        return
    
    json_files = list(directory.glob("*.json"))
    
    for json_file in json_files:
        if json_file.name.startswith("scout_"):
            continue
            
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
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
            
            language = detect_language(host_name)
            country = detect_country(host_name)
            source_block = detect_source_block(host_name, language, dir_name)
            source_type = detect_source_type(host_name, source_block)
            dedup_key = generate_dedup_key(title, date or 'unknown', host_name)
            
            if dedup_key in seen_dedup_keys:
                continue
            seen_dedup_keys.add(dedup_key)
            
            # Базовая аннотация
            narrative_stage = estimate_narrative_stage(title, snippet)
            sentiment = estimate_sentiment(title, snippet)
            frame_type = estimate_frame(title, snippet)
            blame_present = detect_blame(title, snippet, narrative_stage)
            systemic_risk = detect_systemic_risk(title, snippet, narrative_stage)
            
            # НОВЫЕ КОЭФФИЦИЕНТЫ
            source_officiality = get_source_officiality_score(host_name, source_block)
            article_tone = get_article_tone(title, snippet)
            situation_framing = get_situation_framing(title, snippet)
            forecast_presence = get_forecast_presence(title, snippet)
            forecast_detail = get_forecast_detail_level(title, snippet)
            anxiety_level = get_anxiety_level(title, snippet, narrative_stage)
            predictive_signal = get_predictive_signal(title, snippet, narrative_stage, forecast_presence)
            
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
                'source_officiality': source_officiality,
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
                'article_tone': article_tone,
                'situation_framing': situation_framing,
                'forecast_presence': forecast_presence,
                'forecast_detail': forecast_detail,
                'predictive_signal': predictive_signal,
                'collected_at': datetime.now().isoformat()
            }
            
            all_materials.append(material)

def main():
    all_materials = []
    seen_dedup_keys = set()
    
    directories = [
        (BASE_DIR / 'newsapi', 'newsapi'),
        (BASE_DIR / 'russian', 'russian'),
        (BASE_DIR / 'telegram', 'telegram'),
        (BASE_DIR / 'official', 'official'),
    ]
    
    for directory, dir_name in directories:
        print(f"Обработка {dir_name}...")
        process_directory(directory, all_materials, seen_dedup_keys, dir_name)
    
    if all_materials:
        output_file = PROCESSED_DIR / 'media_corpus_annotated.csv'
        
        fieldnames = [
            'case_id', 'case_name', 'case_type', 'material_id',
            'source_name', 'source_country', 'source_language', 
            'source_block', 'source_type', 'source_officiality',
            'published_at', 'title', 'url', 'description',
            'query_used', 'window', 'narrative_stage', 'sentiment',
            'anxiety_level', 'frame_type', 'blame_present', 'systemic_risk',
            'article_tone', 'situation_framing', 'forecast_presence',
            'forecast_detail', 'predictive_signal', 'collected_at'
        ]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_materials)
        
        print(f"\n{'='*60}")
        print(f"РАСШИРЕННЫЙ КОРПУС С ПРЕДИКТИВНЫМИ ИНДИКАТОРАМИ")
        print(f"{'='*60}")
        print(f"Всего материалов: {len(all_materials)}")
        print(f"Сохранено в: {output_file}")
        
        # Статистика по новым полям
        print("\n--- НОВЫЕ КОЭФФИЦИЕНТЫ ---")
        
        # Официальность
        off = {}
        for m in all_materials:
            o = m['source_officiality']
            off[o] = off.get(o, 0) + 1
        print("\nОфициальность источника (0-5):")
        for o in sorted(off.keys()):
            label = {0: 'блог/соцсеть', 1: 'альтернат.СМИ', 2: 'независ.СМИ',
                     3: 'мейнстрим', 4: 'госСМИ', 5: 'офиц.орган'}
            print(f"  {o} ({label.get(o, '')}): {off[o]}")
        
        # Тон статьи
        tones = {}
        for m in all_materials:
            t = m['article_tone']
            tones[t] = tones.get(t, 0) + 1
        print("\nТон статьи:")
        for t, c in sorted(tones.items(), key=lambda x: -x[1]):
            print(f"  {t}: {c} ({c*100/len(all_materials):.1f}%)")
        
        # Подача ситуации
        framing = {}
        for m in all_materials:
            f = m['situation_framing']
            framing[f] = framing.get(f, 0) + 1
        print("\nПодача ситуации:")
        for f, c in sorted(framing.items(), key=lambda x: -x[1]):
            print(f"  {f}: {c} ({c*100/len(all_materials):.1f}%)")
        
        # Прогноз
        forecasts = {}
        for m in all_materials:
            f = m['forecast_presence']
            forecasts[f] = forecasts.get(f, 0) + 1
        print("\nНаличие прогноза:")
        for f, c in sorted(forecasts.items(), key=lambda x: -x[1]):
            print(f"  {f}: {c} ({c*100/len(all_materials):.1f}%)")
        
        # Предиктивные сигналы
        signals = {}
        for m in all_materials:
            s = m['predictive_signal']
            signals[s] = signals.get(s, 0) + 1
        print("\nПредиктивные сигналы:")
        for s, c in sorted(signals.items(), key=lambda x: -x[1]):
            print(f"  {s}: {c} ({c*100/len(all_materials):.1f}%)")

if __name__ == '__main__':
    main()
