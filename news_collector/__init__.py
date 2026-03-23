"""명심 스토리를 위한 뉴스 수집 및 대본 생성 모듈"""

from news_collector.categories import CATEGORIES
from news_collector.collector import NewsCollector
from news_collector.script_generator import ScriptGenerator

__all__ = ["CATEGORIES", "NewsCollector", "ScriptGenerator"]
