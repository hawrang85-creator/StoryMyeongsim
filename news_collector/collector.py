"""뉴스 수집 핵심 모듈"""

import json
import os
from datetime import datetime

import feedparser
import requests
from bs4 import BeautifulSoup

from news_collector.categories import CATEGORIES

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


class NewsArticle:
    """수집된 뉴스 기사"""

    def __init__(self, title, link, summary, published, source, category):
        self.title = title
        self.link = link
        self.summary = summary
        self.published = published
        self.source = source
        self.category = category

    def to_dict(self):
        return {
            "title": self.title,
            "link": self.link,
            "summary": self.summary,
            "published": self.published,
            "source": self.source,
            "category": self.category,
        }


class NewsCollector:
    """카테고리별 뉴스 수집기"""

    def __init__(self, categories=None):
        self.categories = categories or list(CATEGORIES.keys())
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; StoryMyeongsim/1.0)"
        }

    def collect_from_rss(self, category_key):
        """RSS 피드에서 뉴스 수집"""
        category = CATEGORIES.get(category_key)
        if not category:
            print(f"알 수 없는 카테고리: {category_key}")
            return []

        articles = []
        for feed_url in category["rss_feeds"]:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:10]:
                    article = NewsArticle(
                        title=entry.get("title", ""),
                        link=entry.get("link", ""),
                        summary=entry.get("summary", ""),
                        published=entry.get("published", ""),
                        source=feed.feed.get("title", feed_url),
                        category=category["name"],
                    )
                    articles.append(article)
            except Exception as e:
                print(f"RSS 수집 오류 ({feed_url}): {e}")

        return articles

    def collect_from_naver(self, category_key, count=10):
        """네이버 뉴스 검색으로 수집 (웹 스크래핑)"""
        category = CATEGORIES.get(category_key)
        if not category:
            print(f"알 수 없는 카테고리: {category_key}")
            return []

        articles = []
        query = "+OR+".join(category["keywords"][:3])
        url = f"https://search.naver.com/search.naver?where=news&query={query}&sort=1"

        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            news_items = soup.select("div.news_area")[:count]
            for item in news_items:
                title_el = item.select_one("a.news_tit")
                desc_el = item.select_one("div.news_dsc")
                source_el = item.select_one("a.info.press")

                if title_el:
                    article = NewsArticle(
                        title=title_el.get_text(strip=True),
                        link=title_el.get("href", ""),
                        summary=desc_el.get_text(strip=True) if desc_el else "",
                        published=datetime.now().strftime("%Y-%m-%d"),
                        source=source_el.get_text(strip=True) if source_el else "",
                        category=category["name"],
                    )
                    articles.append(article)
        except Exception as e:
            print(f"네이버 뉴스 수집 오류: {e}")

        return articles

    def collect(self, category_key, method="rss"):
        """지정된 카테고리의 뉴스 수집"""
        if method == "rss":
            return self.collect_from_rss(category_key)
        elif method == "naver":
            return self.collect_from_naver(category_key)
        else:
            print(f"지원하지 않는 수집 방법: {method}")
            return []

    def collect_all(self, method="rss"):
        """모든 카테고리의 뉴스 수집"""
        all_articles = {}
        for category_key in self.categories:
            category_name = CATEGORIES[category_key]["name"]
            print(f"[{category_name}] 뉴스 수집 중...")
            articles = self.collect(category_key, method=method)
            all_articles[category_key] = articles
            print(f"  -> {len(articles)}건 수집 완료")
        return all_articles

    def save(self, articles_by_category, filename=None):
        """수집된 뉴스를 JSON 파일로 저장"""
        os.makedirs(DATA_DIR, exist_ok=True)

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"news_{timestamp}.json"

        filepath = os.path.join(DATA_DIR, filename)

        data = {
            "collected_at": datetime.now().isoformat(),
            "categories": {},
        }
        for cat_key, articles in articles_by_category.items():
            cat_name = CATEGORIES[cat_key]["name"]
            data["categories"][cat_name] = [a.to_dict() for a in articles]

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"저장 완료: {filepath}")
        return filepath
