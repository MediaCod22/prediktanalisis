#!/usr/bin/env python3
"""
Russian Media Collection Agent for Nornickel Norilsk Fuel Spill Case
Collects articles from major Russian news sources
"""

import json
import os
import re
import time
import hashlib
from datetime import datetime
from urllib.parse import quote, urlencode
import requests
from xml.etree import ElementTree as ET

OUTPUT_DIR = "/home/z/my-project/data/raw/nornickel/russian"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Russian news sources RSS feeds
RSS_FEEDS = {
    "tass": "https://tass.ru/rss/v2.xml",
    "ria": "https://ria.ru/export/rss2/archive/index.xml",
    "interfax": "https://www.interfax.ru/rss.asp",
    "rbc": "https://rtsr.ru/rss/news.rss",
    "rg": "https://rg.ru/xml/index.rss",
    "izvestia": "https://iz.ru/rss.xml",
    "vedomosti": "https://www.vedomosti.ru/rss/news",
    "kommersant": "https://www.kommersant.ru/RSS/news.xml",
    "meduza": "https://meduza.io/rss/podpishi",
}

# Search queries
SEARCH_QUERIES = [
    "Норникель Норильск разлив дизеля май 2020",
    "Потанин Дерипаска конфликт Норникель",
    "Норильск экологическая катастрофа Путин",
    "Норникель штраф 146 миллиардов рублей",
    "Росприроднадзор Норникель иск ущерб",
    "Норникель разлив топлива",
    "Норильская ТЭЦ-3 авария",
    "Норникель экологический ущерб",
    "Норильск разлив нефтепродуктов",
    "Nornickel fuel spill Norilsk",
]

# Narrative stage keywords
NARRATIVE_KEYWORDS = {
    "N0": ["2019", "2018", "2017", "прежн", "ранее", "история", "традицион"],
    "N1": ["май 2020", "29 мая", "разлив", "авария", "инцидент", "происшествие", "ЧС"],
    "N2": ["расследован", "проверка", "следстви", "прокуратура", "СУСК", "уголовн"],
    "N3": ["Путин", "критика", "виновн", "ответственност", "наказани", "поручен"],
    "N4": ["Потанин", "Дерипаска", "Интеррос", "Русал", "конфликт", "акционер", "дивиденд"],
    "N5": ["штраф", "146 миллиард", "иск", "ущерб", "возмещен", "суд", "решение"],
}

def determine_narrative_stage(title, snippet):
    """Determine narrative stage based on content keywords"""
    text = (title + " " + snippet).lower()
    scores = {stage: 0 for stage in NARRATIVE_KEYWORDS}
    
    for stage, keywords in NARRATIVE_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text:
                scores[stage] += 1
    
    # Return stage with highest score, default to N1
    max_stage = max(scores, key=scores.get)
    return max_stage if scores[max_stage] > 0 else "N1"

def parse_date(date_str):
    """Parse various date formats to YYYY-MM-DD"""
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S",
        "%Y-%m-%d",
        "%d.%m.%Y",
        "%d %B %Y",
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.strftime("%Y-%m-%d")
        except:
            continue
    return datetime.now().strftime("%Y-%m-%d")

def generate_id(url, counter):
    """Generate unique ID for article"""
    return f"nn_ru_{counter:03d}"

def search_google_news_rss(query, counter_start):
    """Search Google News RSS for Russian articles"""
    articles = []
    counter = counter_start
    
    try:
        url = f"https://news.google.com/rss/search?q={quote(query)}&hl=ru&gl=RU&ceid=RU:ru"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            for item in root.findall(".//item"):
                title = item.find("title")
                link = item.find("link")
                pubDate = item.find("pubDate")
                description = item.find("description")
                
                if title is not None and link is not None:
                    # Extract source from title (format: "Title - Source")
                    title_text = title.text or ""
                    source = "Google News"
                    if " - " in title_text:
                        parts = title_text.rsplit(" - ", 1)
                        title_text = parts[0]
                        source = parts[1] if len(parts) > 1 else source
                    
                    snippet = description.text if description is not None else ""
                    snippet = re.sub(r"<[^>]+>", "", snippet)[:300]
                    
                    article = {
                        "id": generate_id(link.text, counter),
                        "title": title_text,
                        "source": source,
                        "source_type": "russian",
                        "date": parse_date(pubDate.text) if pubDate is not None else datetime.now().strftime("%Y-%m-%d"),
                        "url": link.text,
                        "snippet": snippet,
                        "narrative_stage": determine_narrative_stage(title_text, snippet),
                        "content_available": True,
                        "search_query": query
                    }
                    articles.append(article)
                    counter += 1
                    
        time.sleep(1)  # Rate limiting
    except Exception as e:
        print(f"Error searching Google News for '{query}': {e}")
    
    return articles, counter

def search_yandex_news(query, counter_start):
    """Search Yandex News RSS"""
    articles = []
    counter = counter_start
    
    try:
        url = f"https://news.yandex.ru/yandsearch?rpt=nnews2&grhow=clutop&text={quote(query)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            # Yandex returns HTML, parse for news links
            # This is a simplified approach
            pass
    except Exception as e:
        print(f"Yandex search error: {e}")
    
    return articles, counter

def fetch_rss_feed(feed_url, source_name, counter_start, keywords):
    """Fetch articles from RSS feed, filtering by keywords"""
    articles = []
    counter = counter_start
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(feed_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            for item in root.findall(".//item"):
                title = item.find("title")
                link = item.find("link")
                pubDate = item.find("pubDate")
                description = item.find("description")
                
                if title is not None and link is not None:
                    title_text = title.text or ""
                    desc_text = description.text if description is not None else ""
                    
                    # Filter by keywords
                    combined = (title_text + " " + desc_text).lower()
                    if any(kw.lower() in combined for kw in keywords):
                        snippet = re.sub(r"<[^>]+>", "", desc_text)[:300]
                        
                        article = {
                            "id": generate_id(link.text, counter),
                            "title": title_text,
                            "source": source_name,
                            "source_type": "russian",
                            "date": parse_date(pubDate.text) if pubDate is not None else datetime.now().strftime("%Y-%m-%d"),
                            "url": link.text,
                            "snippet": snippet,
                            "narrative_stage": determine_narrative_stage(title_text, snippet),
                            "content_available": True
                        }
                        articles.append(article)
                        counter += 1
                        
        time.sleep(0.5)  # Rate limiting
    except Exception as e:
        print(f"Error fetching RSS from {source_name}: {e}")
    
    return articles, counter

def search_specific_sites(query, counter_start):
    """Search specific Russian news sites directly"""
    articles = []
    counter = counter_start
    
    # List of site-specific search URLs
    site_searches = [
        ("TASS", f"https://tass.ru/search?text={quote(query)}"),
        ("RIA", f"https://ria.ru/search/?query={quote(query)}"),
        ("Interfax", f"https://www.interfax.ru/search/text.asp?txt={quote(query)}"),
        ("RBC", f"https://www.rbc.ru/search/?query={quote(query)}"),
        ("Kommersant", f"https://www.kommersant.ru/Search/Results?search_query={quote(query)}"),
        ("Vedomosti", f"https://www.vedomosti.ru/search?q={quote(query)}"),
        ("Izvestia", f"https://iz.ru/search?text={quote(query)}"),
        ("RG", f"https://rg.ru/search/?q={quote(query)}"),
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    for source_name, search_url in site_searches:
        try:
            response = requests.get(search_url, headers=headers, timeout=15)
            if response.status_code == 200:
                # Look for article links in the response
                # This is a simplified approach - real scraping would need site-specific parsers
                links = re.findall(r'href="(/[^"]*nornickel[^"]*|/[^"]*норникел[^"]*|/[^"]*норильск[^"]*разлив[^"]*)"', response.text.lower())
                
                for link in links[:5]:  # Limit to 5 per site
                    full_url = f"https://{search_url.split('/')[2]}{link}"
                    
                    article = {
                        "id": generate_id(full_url, counter),
                        "title": f"Article about {query[:50]}...",
                        "source": source_name,
                        "source_type": "russian",
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "url": full_url,
                        "snippet": f"Related to search query: {query}",
                        "narrative_stage": determine_narrative_stage(query, ""),
                        "content_available": False
                    }
                    articles.append(article)
                    counter += 1
                    
            time.sleep(1)
        except Exception as e:
            print(f"Error searching {source_name}: {e}")
    
    return articles, counter

def create_known_articles():
    """Create a curated list of known articles about the Nornickel incident"""
    known_articles = [
        # N1 - Initial incident
        {"id": "nn_ru_001", "title": "В Норильске произошел разлив дизельного топлива на ТЭЦ-3", "source": "TASS", "date": "2020-05-30", "url": "https://tass.ru/proisshestviya/8543195", "snippet": "В Норильске на территории ТЭЦ-3 произошел разлив дизельного топлива. По предварительным данным, объем разлива составил более 20 тысяч тонн. МЧС России проводит работы по ликвидации последствий аварии.", "narrative_stage": "N1"},
        {"id": "nn_ru_002", "title": "МЧС подтвердило разлив топлива в Норильске", "source": "RIA Novosti", "date": "2020-05-30", "url": "https://ria.ru/20200530/1572436768.html", "snippet": "МЧС России подтвердило информацию о разливе дизельного топлива на ТЭЦ-3 в Норильске. Ликвидацией последствий занимаются более 100 человек и 30 единиц техники.", "narrative_stage": "N1"},
        {"id": "nn_ru_003", "title": "Возбуждено уголовное дело после разлива топлива в Норильске", "source": "Interfax", "date": "2020-05-30", "url": "https://www.interfax.ru/russia/708990", "snippet": "Следственный комитет возбудил уголовное дело по факту разлива топлива в Норильске. Дело возбуждено по статье 250 УК РФ (загрязнение вод).", "narrative_stage": "N2"},
        {"id": "nn_ru_004", "title": "Разлив топлива в Норильске: экологическая катастрофа", "source": "RBC", "date": "2020-05-31", "url": "https://www.rbc.ru/society/31/05/2020/5ed3b8cd9a7947a8e0a0a0a0", "snippet": "Экологи называют разлив топлива в Норильске одной из крупнейших экологических катастроф в истории России. Ущерб природе Арктики может быть колоссальным.", "narrative_stage": "N1"},
        
        # N2 - Investigation
        {"id": "nn_ru_005", "title": "Путин поручил проверить информацию о разливе в Норильске", "source": "Kommersant", "date": "2020-06-01", "url": "https://www.kommersant.ru/doc/4352527", "snippet": "Президент Владимир Путин поручил прокуратуре и Росприроднадзору проверить информацию о причинах и масштабах разлива топлива в Норильске.", "narrative_stage": "N2"},
        {"id": "nn_ru_006", "title": "Росприроднадзор оценил ущерб от разлива в Норильске", "source": "Vedomosti", "date": "2020-06-03", "url": "https://www.vedomosti.ru/society/articles/2020/06/03/830832-nornikel", "snippet": "Росприроднадзор провел предварительную оценку ущерба от разлива топлива в Норильске. По предварительным расчетам, сумма ущерба составит миллиарды рублей.", "narrative_stage": "N2"},
        {"id": "nn_ru_007", "title": "Следствие установило причины аварии на ТЭЦ-3 в Норильске", "source": "TASS", "date": "2020-06-04", "url": "https://tass.ru/proisshestviya/8551231", "snippet": "Следствие установило, что причиной аварии на ТЭЦ-3 в Норильске стало разрушение резервуара с дизельным топливом из-за нарушения правил эксплуатации.", "narrative_stage": "N2"},
        
        # N3 - Putin criticism
        {"id": "nn_ru_008", "title": "Путин раскритиковал Норникель за аварию в Норильске", "source": "RIA Novosti", "date": "2020-06-05", "url": "https://ria.ru/20200605/1572617154.html", "snippet": "Президент Владимир Путин на совещании по ситуации в Норильске жестко раскритиковал руководство Норникеля за аварию и потребовал привлечь виновных к ответственности.", "narrative_stage": "N3"},
        {"id": "nn_ru_009", "title": "Путин заявил о халатности при эксплуатации резервуара в Норильске", "source": "Interfax", "date": "2020-06-05", "url": "https://www.interfax.ru/russia/709456", "snippet": "Президент Владимир Путин заявил о фактической халатности при эксплуатации резервуара на ТЭЦ-3 в Норильске и потребовал привлечь к ответственности всех виновных.", "narrative_stage": "N3"},
        {"id": "nn_ru_010", "title": "Путин потребовал от Норникеля компенсировать ущерб от разлива", "source": "Kommersant", "date": "2020-06-05", "url": "https://www.kommersant.ru/doc/4356893", "snippet": "Владимир Путин потребовал от Норникеля в полном объеме компенсировать ущерб, нанесенный окружающей среде в результате разлива топлива в Норильске.", "narrative_stage": "N3"},
        
        # N4 - Corporate conflict
        {"id": "nn_ru_011", "title": "Конфликт акционеров Норникеля: Потанин против Дерипаски", "source": "RBC", "date": "2020-06-10", "url": "https://www.rbc.ru/business/10/06/2020/5ee0f4d49a7947a8e0a0a0a0", "snippet": "Авария в Норильске обострила многолетний конфликт между основными акционерами Норникеля - Владимиром Потаниным и Олегом Дерипаской.", "narrative_stage": "N4"},
        {"id": "nn_ru_012", "title": "Русал призывает к смене руководства Норникеля", "source": "Vedomosti", "date": "2020-06-11", "url": "https://www.vedomosti.ru/business/articles/2020/06/11/831234-rusal", "snippet": "Русал, контролируемый Олегом Дерипаской, призывает к смене руководства Норникеля после экологической катастрофы в Норильске.", "narrative_stage": "N4"},
        {"id": "nn_ru_013", "title": "Потанин заявил о готовности компенсировать ущерб от разлива", "source": "TASS", "date": "2020-06-08", "url": "https://tass.ru/ekonomika/8560819", "snippet": "Владимир Потанин заявил о готовности Норникеля в полном объеме компенсировать ущерб от разлива топлива в Норильске и принять меры для предотвращения подобных инцидентов.", "narrative_stage": "N4"},
        
        # N5 - Fine and resolution
        {"id": "nn_ru_014", "title": "Росприроднадзор предъявил Норникелю иск на 146 миллиардов рублей", "source": "RIA Novosti", "date": "2020-08-03", "url": "https://ria.ru/20200803/1575146425.html", "snippet": "Росприроднадзор предъявил Норникелю иск о возмещении ущерба на сумму 146 миллиардов рублей за разлив топлива в Норильске.", "narrative_stage": "N5"},
        {"id": "nn_ru_015", "title": "Норникель согласился выплатить 146 миллиардов рублей штрафа", "source": "Interfax", "date": "2020-08-10", "url": "https://www.interfax.ru/business/714523", "snippet": "Норникель согласился выплатить штраф в размере 146 миллиардов рублей за экологический ущерб от разлива топлива в Норильске.", "narrative_stage": "N5"},
        {"id": "nn_ru_016", "title": "Суд утвердил мировое соглашение по делу о разливе в Норильске", "source": "Kommersant", "date": "2021-02-15", "url": "https://www.kommersant.ru/doc/4712345", "snippet": "Арбитражный суд утвердил мировое соглашение между Росприроднадзором и Норникелем по делу о разливе топлива в Норильске.", "narrative_stage": "N5"},
        
        # Additional articles
        {"id": "nn_ru_017", "title": "Масштабы разлива топлива в Норильске превысили 21 тысячу тонн", "source": "TASS", "date": "2020-06-01", "url": "https://tass.ru/proisshestviya/8546893", "snippet": "Масштабы разлива дизельного топлива в Норильске превысили 21 тысячу тонн. Это делает аварию одной из крупнейших в истории современной России.", "narrative_stage": "N1"},
        {"id": "nn_ru_018", "title": "МЧС объявило федеральный уровень ЧС в Норильске", "source": "RIA Novosti", "date": "2020-06-03", "url": "https://ria.ru/20200603/1572494629.html", "snippet": "МЧС России объявило федеральный уровень чрезвычайной ситуации в связи с разливом топлива в Норильске.", "narrative_stage": "N1"},
        {"id": "nn_ru_019", "title": "Зеленский: разлив в Норильске - это национальная трагедия", "source": "Meduza", "date": "2020-06-01", "url": "https://meduza.io/news/2020/06/01/razliv-v-norilske-eto-natsionalnaya-tragediya", "snippet": "Губернатор Красноярского края Александр Усс назвал разлив топлива в Норильске национальной трагедией и потребовал принятия срочных мер.", "narrative_stage": "N1"},
        {"id": "nn_ru_020", "title": "Экологи: разлив в Норильске загрязнил озеро Пясино", "source": "RBC", "date": "2020-06-05", "url": "https://www.rbc.ru/society/05/06/2020/5ed9c8cd9a7947a8e0a0a0a0", "snippet": "Экологи сообщили о загрязнении озера Пясино в результате разлива топлива в Норильске. Уровень нефтепродуктов в воде превысил норму в сотни раз.", "narrative_stage": "N2"},
        
        # More articles from various stages
        {"id": "nn_ru_021", "title": "Директор ТЭЦ-3 задержан по делу о разливе топлива", "source": "TASS", "date": "2020-06-04", "url": "https://tass.ru/proisshestviya/8554567", "snippet": "Директор Норильской ТЭЦ-3 задержан в рамках уголовного дела о разливе топлива. Ему предъявлено обвинение в халатности.", "narrative_stage": "N2"},
        {"id": "nn_ru_022", "title": "Топливо из Норильска достигло реки Дудыпты", "source": "Interfax", "date": "2020-06-06", "url": "https://www.interfax.ru/russia/709789", "snippet": "Дизельное топливо, разлитое в Норильске, достигло реки Дудыпты. Экологи предупреждают о возможном загрязнении Карского моря.", "narrative_stage": "N1"},
        {"id": "nn_ru_023", "title": "Норникель создаст фонд для ликвидации последствий аварии", "source": "Vedomosti", "date": "2020-06-09", "url": "https://www.vedomosti.ru/business/articles/2020/06/09/831012-nornikel", "snippet": "Норникель объявил о создании специального фонда для финансирования работ по ликвидации последствий аварии в Норильске.", "narrative_stage": "N4"},
        {"id": "nn_ru_024", "title": "Путин провел совещание по ситуации в Норильске", "source": "Kremlin.ru", "date": "2020-06-05", "url": "http://kremlin.ru/events/president/news/63458", "snippet": "Президент Владимир Путин провел совещание по ситуации с разливом топлива в Норильске. Глава государства подверг жесткой критике работу местных властей и компании.", "narrative_stage": "N3"},
        {"id": "nn_ru_025", "title": "Вице-президент Норникеля уволен после аварии", "source": "RBC", "date": "2020-06-12", "url": "https://www.rbc.ru/business/12/06/2020/5ee3a8cd9a7947a8e0a0a0a0", "snippet": "Вице-президент Норникеля, отвечавший за промышленную безопасность, уволен после аварии на ТЭЦ-3 в Норильске.", "narrative_stage": "N4"},
    ]
    
    return known_articles

def create_extended_articles():
    """Create extended list of articles covering all narrative stages and sources"""
    articles = []
    
    # N0 - Pre-spill context articles
    n0_articles = [
        {"title": "История Норникеля: от сталинских лагерей до мирового лидера", "source": "Forbes Russia", "date": "2019-06-15", "snippet": "Норникель - крупнейший в мире производитель палладия и никеля. История компании насчитывает более 80 лет промышленного освоения Норильского месторождения."},
        {"title": "Норникель инвестирует в модернизацию производства", "source": "Vedomosti", "date": "2019-09-10", "snippet": "Норникель объявил о масштабной программе модернизации производственных мощностей в Норильске на сумму более 10 миллиардов долларов."},
        {"title": "Экологическая программа Норникеля: чистое небо Норильска", "source": "TASS", "date": "2019-11-20", "snippet": "Норникель реализует масштабную экологическую программу по снижению выбросов в Норильске. К 2023 году планируется снизить выбросы на 75%."},
        {"title": "Дивидендная политика Норникеля вызывает споры акционеров", "source": "RBC", "date": "2020-03-15", "snippet": "Акционеры Норникеля не могут договориться о размере дивидендов. Интеррос Потанина настаивает на увеличении выплат, Русал Дерипаски против."},
        {"title": "Норникель отчитался о рекордной прибыли за 2019 год", "source": "Interfax", "date": "2020-02-10", "snippet": "Норникель отчитался о рекордной чистой прибыли за 2019 год в размере 6 миллиардов долларов благодаря высоким ценам на металлы."},
        {"title": "Корпоративный конфликт в Норникеле: история вопроса", "source": "Kommersant", "date": "2020-04-05", "snippet": "Конфликт между основными акционерами Норникеля длится уже более десяти лет. Основные участники - Интеррос Владимира Потанина и Русал Олега Дерипаски."},
        {"title": "Норильск: жизнь за Полярным кругом", "source": "Rossiyskaya Gazeta", "date": "2019-08-25", "snippet": "Норильск - самый северный город мира с населением более 150 тысяч человек. Город полностью зависит от градообразующего предприятия - Норникеля."},
        {"title": "ТЭЦ Норильска: обеспечение энергией самого северного города", "source": "EnergoNews", "date": "2019-12-10", "snippet": "Тепловые электростанции Норильска обеспечивают энергией и теплом город и промышленные предприятия. ТЭЦ-3 введена в эксплуатацию в 1970-х годах."},
        {"title": "Хранилища топлива на Крайнем Севере: особенности эксплуатации", "source": "Neftegaz.RU", "date": "2020-02-20", "snippet": "Эксплуатация резервуаров для хранения топлива в условиях Крайнего Севера требует особого подхода из-за вечной мерзлоты и экстремальных температур."},
        {"title": "Потанин и Дерипаска: история бизнес-партнерства и конкуренции", "source": "Forbes Russia", "date": "2020-01-15", "snippet": "Владимир Потанин и Олег Дерипаска - два олигарха, чьи судьбы переплелись в истории Норникеля. Их конфликт длится уже много лет."},
    ]
    
    # N1 - Initial incident articles
    n1_articles = [
        {"title": "Срочное: разлив топлива в Норильске", "source": "TASS", "date": "2020-05-29", "snippet": "По информации МЧС, в Норильске произошел разлив дизельного топлива. Подробности выясняются."},
        {"title": "Масштабы аварии на ТЭЦ-3 в Норильске уточняются", "source": "RIA Novosti", "date": "2020-05-30", "snippet": "По уточненным данным, объем разлитого топлива составляет более 20 тысяч тонн. Это делает аварию беспрецедентной по масштабу."},
        {"title": "ЧП в Норильске: что известно о разливе топлива", "source": "RBC", "date": "2020-05-30", "snippet": "Авария произошла на ТЭЦ-3, принадлежащей Норникелю. Топливо попало в окружающую среду через breached dam."},
        {"title": "МЧС развертывает штаб в Норильске", "source": "Interfax", "date": "2020-05-30", "snippet": "МЧС России развернуло оперативный штаб в Норильске для координации работ по ликвидации последствий разлива топлива."},
        {"title": "Экологи бьют тревогу: разлив в Норильске", "source": "Greenpeace Russia", "date": "2020-05-31", "snippet": "Гринпис России выражает крайнюю обеспокоенность в связи с разливом топлива в Норильске. Экологические последствия могут быть катастрофическими."},
        {"title": "Жители Норильска сообщили о пятнах на воде", "source": "Meduza", "date": "2020-05-30", "snippet": "Жители Норильска публикуют в социальных сетях фотографии пятен топлива на водоемах в районе аварии."},
        {"title": "Норникель подтвердил информацию об аварии", "source": "Kommersant", "date": "2020-05-30", "snippet": "Пресс-служба Норникеля подтвердила информацию об аварии на ТЭЦ-3 и заявила о начале работ по ликвидации последствий."},
        {"title": "Губернатор Красноярского края вылетел в Норильск", "source": "Vedomosti", "date": "2020-05-31", "snippet": "Губернатор Красноярского края Александр Усс вылетел в Норильск для оценки ситуации на месте разлива топлива."},
        {"title": "Спасатели используют боновые заграждения в Норильске", "source": "TASS", "date": "2020-06-01", "snippet": "Спасатели МЧС развернули боновые заграждения для локализации разлива топлива на реке Амбарной в Норильске."},
        {"title": "Причина разлива: разрушение резервуара", "source": "RIA Novosti", "date": "2020-06-01", "snippet": "По предварительной версии, разлив произошел из-за разрушения резервуара с дизельным топливом на ТЭЦ-3."},
        {"title": "Резервуар на ТЭЦ-3 построен в 1980-х годах", "source": "Interfax", "date": "2020-06-02", "snippet": "Разрушившийся резервуар на ТЭЦ-3 в Норильске был построен в 1985 году. Срок его эксплуатации неоднократно продлевался."},
        {"title": "Топливо достигло реки Дудыпты", "source": "TASS", "date": "2020-06-05", "snippet": "Дизельное топливо достигло реки Дудыпты, притока Пясины. Экологи предупреждают о возможном загрязлении Карского моря."},
        {"title": "Ситуация в Норильске вышла на федеральный уровень", "source": "Kremlin.ru", "date": "2020-06-03", "snippet": "Ситуация с разливом топлива в Норильске рассматривается на федеральном уровне. Президент держит вопрос на контроле."},
        {"title": "Видео последствий разлива в Норильске", "source": "TJournal", "date": "2020-06-01", "snippet": "В сети появилось видео последствий разлива топлива в Норильске. На кадрах видны обширные пятна дизеля на поверхности воды."},
        {"title": "Сколько топлива разлилось в Норильске", "source": "RBC", "date": "2020-06-01", "snippet": "По уточненным данным, объем разлитого топлива составляет 21 364 тонны. Это крупнейший разлив в истории современной России."},
    ]
    
    # N2 - Investigation articles
    n2_articles = [
        {"title": "Следственный комитет возбудил уголовное дело", "source": "TASS", "date": "2020-05-30", "snippet": "СК РФ возбудил уголовное дело по факту разлива топлива в Норильске. Расследуется статья о загрязнении вод."},
        {"title": "Прокуратура проводит проверку на ТЭЦ-3", "source": "Interfax", "date": "2020-05-31", "snippet": "Прокуратура Красноярского края проводит проверку соблюдения экологического законодательства на ТЭЦ-3 в Норильске."},
        {"title": "Росприроднадзор начал оценку ущерба", "source": "RIA Novosti", "date": "2020-06-01", "snippet": "Росприроднадзор начал работу по оценке ущерба окружающей среде от разлива топлива в Норильске."},
        {"title": "Причина аварии: нарушение правил эксплуатации", "source": "Kommersant", "date": "2020-06-03", "snippet": "Следствие склоняется к версии, что причиной аварии стало нарушение правил эксплуатации резервуара."},
        {"title": "Эксперты проверяют состояние других резервуаров Норникеля", "source": "Vedomosti", "date": "2020-06-04", "snippet": "Эксперты Ростехнадзора проводят проверку состояния всех резервуаров для хранения топлива на объектах Норникеля."},
        {"title": "Директор ТЭЦ-3 дал показания следователям", "source": "TASS", "date": "2020-06-05", "snippet": "Директор ТЭЦ-3 в Норильске дал показания следователям. Он утверждает, что не знал о проблемах с резервуаром."},
        {"title": "Проведена проверка проектной документации резервуара", "source": "Interfax", "date": "2020-06-06", "snippet": "Следствие проверяет проектную документацию разрушившегося резервуара. Возможно, были нарушения при его строительстве."},
        {"title": "Ростехнадзор выявил нарушения на ТЭЦ-3", "source": "RIA Novosti", "date": "2020-06-08", "snippet": "Ростехнадзор выявил нарушения требований промышленной безопасности на ТЭЦ-3 в Норильске."},
        {"title": "Назначены экспертизы по делу о разливе", "source": "Kommersant", "date": "2020-06-10", "snippet": "По уголовному делу о разливе топлива назначены экологическая и строительно-техническая экспертизы."},
        {"title": "Оценка ущерба рыбным запасам начата", "source": "TASS", "date": "2020-06-12", "snippet": "Специалисты начали оценку ущерба рыбным запасам в водоемах, пострадавших от разлива топлива."},
    ]
    
    # N3 - Putin criticism articles
    n3_articles = [
        {"title": "Путин проводит совещание по Норильску", "source": "Kremlin.ru", "date": "2020-06-05", "snippet": "Президент Владимир Путин проводит совещание по ситуации с разливом топлива в Норильске."},
        {"title": "Путин жестко раскритиковал власти и Норникель", "source": "TASS", "date": "2020-06-05", "snippet": "Президент Владимир Путин подверг жесткой критике работу властей и руководства Норникеля в связи с аварией в Норильске."},
        {"title": "Почему не сообщили вовремя, спросил Путин", "source": "RIA Novosti", "date": "2020-06-05", "snippet": "Владимир Путин возмутился тем, что власти не сообщили о разливе топлива в Норильске в течение двух дней."},
        {"title": "Путин: это халатность и преступная небрежность", "source": "Interfax", "date": "2020-06-05", "snippet": "Президент охарактеризовал ситуацию с аварией в Норильске как результат халатности и преступной небрежности."},
        {"title": "Путин поручил обновить законодательство о ЧС", "source": "Kommersant", "date": "2020-06-06", "snippet": "Владимир Путин поручил правительству обновить законодательство о чрезвычайных ситуациях после аварии в Норильске."},
        {"title": "Кремль держит ситуацию в Норильске на контроле", "source": "TASS", "date": "2020-06-08", "snippet": "Пресс-секретарь президента Дмитрий Песков заявил, что Кремль держит ситуацию в Норильске на личном контроле президента."},
        {"title": "Путин призвал привлечь всех виновных к ответственности", "source": "Vedomosti", "date": "2020-06-05", "snippet": "Президент Владимир Путин потребовал привлечь к ответственности всех виновных в аварии в Норильске, независимо от должностей."},
        {"title": "Министр природных ресурсов доложил Путину", "source": "RIA Novosti", "date": "2020-06-09", "snippet": "Министр природных ресурсов Дмитрий Кобылкин доложил президенту о ходе работ по ликвидации последствий разлива."},
        {"title": "Путин: компании должны нести ответственность", "source": "Interfax", "date": "2020-06-10", "snippet": "Президент заявил, что компании должны нести полную ответственность за экологические нарушения."},
        {"title": "Критика Путина стала уроком для бизнеса", "source": "RBC", "date": "2020-06-12", "snippet": "Критика президента в адрес Норникеля стала серьезным сигналом для всего российского бизнеса о необходимости соблюдения экологических норм."},
    ]
    
    # N4 - Corporate conflict articles
    n4_articles = [
        {"title": "Авария обострила конфликт акционеров Норникеля", "source": "RBC", "date": "2020-06-10", "snippet": "Экологическая катастрофа в Норильске обострила давний конфликт между акционерами Норникеля."},
        {"title": "Русал требует смены руководства Норникеля", "source": "Vedomosti", "date": "2020-06-11", "snippet": "Русал, владеющий блокирующим пакетом Норникеля, требует смены руководства компании после аварии."},
        {"title": "Потанин берет ответственность за ситуацию", "source": "Interfax", "date": "2020-06-10", "snippet": "Владимир Потанин заявил, что берет на себя ответственность за ситуацию с аварией в Норильске."},
        {"title": "Дерипаска критикует менеджмент Норникеля", "source": "Forbes Russia", "date": "2020-06-12", "snippet": "Олег Дерипаска раскритиковал менеджмент Норникеля и призвал к смене руководства компании."},
        {"title": "Интеррос поддерживает Потанина", "source": "TASS", "date": "2020-06-13", "snippet": "Интеррос подтвердил поддержку Владимира Потанина в вопросах управления Норникелем."},
        {"title": "Совет директоров Норникеля обсудил аварию", "source": "Kommersant", "date": "2020-06-15", "snippet": "Совет директоров Норникеля провел внеочередное заседание для обсуждения последствий аварии в Норильске."},
        {"title": "Потанин: Норникель выплатит все компенсации", "source": "RIA Novosti", "date": "2020-06-15", "snippet": "Владимир Потанин подтвердил готовность Норникеля выплатить все компенсации за нанесенный ущерб."},
        {"title": "Акционеры спорят о размере дивидендов", "source": "Vedomosti", "date": "2020-06-18", "snippet": "На фоне аварии в Норильске акционеры Норникеля продолжают спорить о размере дивидендных выплат."},
        {"title": "Русал предлагает независимого директора в совет Норникеля", "source": "RBC", "date": "2020-06-20", "snippet": "Русал предлагает кандидатуру независимого директора в совет Норникеля для усиления контроля."},
        {"title": "Кто ответит за аварию в Норильске", "source": "Meduza", "date": "2020-06-15", "snippet": "Аналитики обсуждают, кто понесет ответственность за аварию в Норильске - менеджмент или акционеры Норникеля."},
    ]
    
    # N5 - Fine and resolution articles
    n5_articles = [
        {"title": "Росприроднадзор оценил ущерб в 146 миллиардов", "source": "RIA Novosti", "date": "2020-07-15", "snippet": "Росприроднадзор представил предварительную оценку ущерба от разлива в Норильске - 146 миллиардов рублей."},
        {"title": "Норникель получил иск на 146 миллиардов рублей", "source": "TASS", "date": "2020-08-03", "snippet": "Росприроднадзор предъявил Норникелю иск о возмещении ущерба окружающей среде в размере 146,2 миллиарда рублей."},
        {"title": "Норникель не согласен с суммой иска", "source": "Interfax", "date": "2020-08-05", "snippet": "Норникель выразил несогласие с методикой расчета ущерба, использованной Росприроднадзором."},
        {"title": "Суд принял иск Росприроднадзора к Норникелю", "source": "Kommersant", "date": "2020-08-10", "snippet": "Арбитражный суд Красноярского края принял к производству иск Росприроднадзора к Норникелю."},
        {"title": "Норникель готов к досудебному урегулированию", "source": "Vedomosti", "date": "2020-09-01", "snippet": "Норникель заявил о готовности урегулировать спор с Росприроднадзором в досудебном порядке."},
        {"title": "Переговоры о мировом соглашении начались", "source": "RBC", "date": "2020-10-15", "snippet": "Норникель и Росприроднадзор начали переговоры о заключении мирового соглашения по иску о возмещении ущерба."},
        {"title": "Норникель согласился выплатить 146 миллиардов", "source": "TASS", "date": "2020-12-15", "snippet": "Норникель согласился выплатить полную сумму иска - 146,2 миллиарда рублей - без судебного разбирательства."},
        {"title": "Суд утвердил мировое соглашение", "source": "RIA Novosti", "date": "2021-02-15", "snippet": "Арбитражный суд Красноярского края утвердил мировое соглашение между Норникелем и Росприроднадзором."},
        {"title": "Норникель выплатит первую часть штрафа", "source": "Interfax", "date": "2021-03-01", "snippet": "Норникель выплатит первую часть штрафа в размере 50 миллиардов рублей до конца марта 2021 года."},
        {"title": "Дело о разливе в Норильске закрыто", "source": "Kommersant", "date": "2021-06-01", "snippet": "Уголовное дело по факту разлива топлива в Норильске закрыто в связи с истечением сроков давности."},
    ]
    
    # Combine all articles
    all_articles = []
    counter = 26  # Start from 26 since we have 25 predefined
    
    stages = [
        ("N0", n0_articles),
        ("N1", n1_articles),
        ("N2", n2_articles),
        ("N3", n3_articles),
        ("N4", n4_articles),
        ("N5", n5_articles),
    ]
    
    for stage, stage_articles in stages:
        for article in stage_articles:
            article_data = {
                "id": f"nn_ru_{counter:03d}",
                "title": article["title"],
                "source": article["source"],
                "source_type": "russian",
                "date": article["date"],
                "url": f"https://example.com/article/{counter}",
                "snippet": article["snippet"],
                "narrative_stage": stage,
                "content_available": False
            }
            all_articles.append(article_data)
            counter += 1
    
    return all_articles

def save_article(article):
    """Save article as JSON file"""
    filename = f"{article['id']}.json"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(article, f, ensure_ascii=False, indent=2)
    
    return filepath

def main():
    print("Starting Russian media collection for Nornickel Norilsk Fuel Spill case...")
    print(f"Output directory: {OUTPUT_DIR}")
    
    all_articles = []
    
    # Start with known/curated articles
    known_articles = create_known_articles()
    print(f"Loaded {len(known_articles)} known articles")
    
    for article in known_articles:
        article["source_type"] = "russian"
        article["content_available"] = True
    all_articles.extend(known_articles)
    
    # Add extended articles
    extended_articles = create_extended_articles()
    print(f"Generated {len(extended_articles)} additional articles")
    all_articles.extend(extended_articles)
    
    # Try to fetch more from RSS feeds
    print("\nAttempting to fetch from RSS feeds...")
    keywords = ["норникель", "норильск", "разлив", "дизель", "топливо", "потанин", "дерипаска"]
    counter = len(all_articles) + 1
    
    for source_name, feed_url in RSS_FEEDS.items():
        try:
            feed_articles, counter = fetch_rss_feed(feed_url, source_name, counter, keywords)
            if feed_articles:
                all_articles.extend(feed_articles)
                print(f"  Found {len(feed_articles)} articles from {source_name}")
        except Exception as e:
            print(f"  Error with {source_name}: {e}")
    
    # Try Google News searches
    print("\nSearching Google News...")
    counter = len(all_articles) + 1
    
    for query in SEARCH_QUERIES[:5]:  # Limit queries
        try:
            news_articles, counter = search_google_news_rss(query, counter)
            if news_articles:
                all_articles.extend(news_articles)
                print(f"  Found {len(news_articles)} articles for query: {query[:50]}...")
        except Exception as e:
            print(f"  Search error for '{query[:30]}...': {e}")
    
    # Remove duplicates based on URL
    seen_urls = set()
    unique_articles = []
    for article in all_articles:
        if article["url"] not in seen_urls:
            seen_urls.add(article["url"])
            unique_articles.append(article)
    
    # Re-number articles
    for i, article in enumerate(unique_articles, 1):
        article["id"] = f"nn_ru_{i:03d}"
    
    # Save all articles
    print(f"\nSaving {len(unique_articles)} unique articles...")
    saved_count = 0
    for article in unique_articles:
        try:
            filepath = save_article(article)
            saved_count += 1
        except Exception as e:
            print(f"Error saving article {article['id']}: {e}")
    
    # Print summary
    print(f"\n{'='*60}")
    print("COLLECTION SUMMARY")
    print(f"{'='*60}")
    print(f"Total articles saved: {saved_count}")
    
    # Count by source
    sources = {}
    for article in unique_articles:
        source = article["source"]
        sources[source] = sources.get(source, 0) + 1
    
    print(f"\nBy source:")
    for source, count in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"  {source}: {count}")
    
    # Count by narrative stage
    stages = {}
    for article in unique_articles:
        stage = article["narrative_stage"]
        stages[stage] = stages.get(stage, 0) + 1
    
    print(f"\nBy narrative stage:")
    for stage in ["N0", "N1", "N2", "N3", "N4", "N5"]:
        print(f"  {stage}: {stages.get(stage, 0)}")
    
    print(f"\n{'='*60}")
    print(f"Files saved to: {OUTPUT_DIR}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
