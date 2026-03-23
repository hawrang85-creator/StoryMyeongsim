"""Claude API를 활용한 대본 생성 모듈"""

import json
import os
from datetime import datetime

import anthropic

from news_collector.categories import CATEGORIES
from news_collector.prompts import (
    CATEGORY_TONE,
    SCRIPT_PROMPT_TEMPLATE,
    SYSTEM_PROMPT,
)

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts")


class ScriptGenerator:
    """수집된 뉴스를 바탕으로 대본을 생성하는 클래스"""

    def __init__(self, model="claude-sonnet-4-6"):
        self.client = anthropic.Anthropic()
        self.model = model

    def _format_news_for_prompt(self, articles):
        """뉴스 기사 목록을 프롬프트용 텍스트로 변환"""
        lines = []
        for i, article in enumerate(articles, 1):
            a = article if isinstance(article, dict) else article.to_dict()
            lines.append(f"{i}. 제목: {a['title']}")
            if a.get("summary"):
                lines.append(f"   요약: {a['summary']}")
            if a.get("source"):
                lines.append(f"   출처: {a['source']}")
            if a.get("published"):
                lines.append(f"   일시: {a['published']}")
            lines.append("")
        return "\n".join(lines)

    def generate(self, articles, category_key):
        """뉴스 기사를 바탕으로 대본 생성"""
        category = CATEGORIES.get(category_key, {})
        category_name = category.get("name", category_key)

        news_content = self._format_news_for_prompt(articles)

        tone = CATEGORY_TONE.get(category_key, "")
        system = SYSTEM_PROMPT
        if tone:
            system += f"\n\n이번 카테고리 톤: {tone}"

        user_prompt = SCRIPT_PROMPT_TEMPLATE.format(
            category=category_name,
            news_content=news_content,
        )

        print(f"  Claude API로 [{category_name}] 대본 생성 중...")

        message = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user_prompt}],
        )

        script_text = message.content[0].text
        print(f"  -> 대본 생성 완료 ({len(script_text)}자)")
        return script_text

    def generate_all(self, articles_by_category):
        """모든 카테고리의 대본을 생성"""
        scripts = {}
        for cat_key, articles in articles_by_category.items():
            if not articles:
                print(f"  [{CATEGORIES[cat_key]['name']}] 뉴스가 없어 건너뜁니다.")
                continue
            scripts[cat_key] = self.generate(articles, cat_key)
        return scripts

    def save(self, scripts, filename=None):
        """생성된 대본을 파일로 저장"""
        os.makedirs(SCRIPTS_DIR, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_files = []

        for cat_key, script_text in scripts.items():
            cat_name = CATEGORIES.get(cat_key, {}).get("name", cat_key)
            fname = filename or f"script_{cat_key}_{timestamp}.txt"
            filepath = os.path.join(SCRIPTS_DIR, fname)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"=== 명심 스토리 대본 ===\n")
                f.write(f"카테고리: {cat_name}\n")
                f.write(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
                f.write(f"{'=' * 40}\n\n")
                f.write(script_text)

            saved_files.append(filepath)
            print(f"  대본 저장: {filepath}")

            # 여러 카테고리일 때 파일명 중복 방지
            filename = None

        return saved_files

    def generate_from_json(self, json_path):
        """저장된 뉴스 JSON 파일에서 대본 생성"""
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        articles_by_category = {}
        for cat_name, articles in data.get("categories", {}).items():
            cat_key = None
            for key, cat in CATEGORIES.items():
                if cat["name"] == cat_name:
                    cat_key = key
                    break
            if cat_key:
                articles_by_category[cat_key] = articles

        return self.generate_all(articles_by_category)
