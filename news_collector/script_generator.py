"""명심Story v4.0 대본 생성 모듈

Claude API로 선택된 뉴스 기반 대본을 자동 생성합니다.
"""

import json
import os
import re
from datetime import datetime

import anthropic

from news_collector.categories import CATEGORIES
from news_collector.prompts import (
    CATEGORY_CONTEXT,
    SCRIPT_PROMPT_TEMPLATE,
    SYSTEM_PROMPT,
)

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts")


class ScriptValidator:
    """명심Story v4.0 무결성 검증"""

    FORBIDDEN_ENDINGS = ["고요", "겁니다", "까요", "을까요", "네요", "는요"]
    FORBIDDEN_PUNCTUATION = [".", ",", "'"]
    VALID_LINEBREAK_ENDINGS = ["죠", "요", "다", "데요", "니다"]

    @staticmethod
    def check_forbidden_endings(script_text):
        found = []
        for ending in ScriptValidator.FORBIDDEN_ENDINGS:
            if ending in script_text:
                found.append(ending)
        return found

    @staticmethod
    def check_punctuation(script_text):
        found = []
        for p in ScriptValidator.FORBIDDEN_PUNCTUATION:
            if p in script_text:
                found.append(p)
        return found

    @staticmethod
    def check_linebreaks(script_text):
        lines = script_text.strip().split("\n")
        violations = []
        for i, line in enumerate(lines[:-1]):
            line = line.rstrip()
            if not line:
                continue
            valid = False
            for ending in ScriptValidator.VALID_LINEBREAK_ENDINGS:
                if line.endswith(ending) or line.endswith(ending + "!"):
                    valid = True
                    break
            if not valid:
                violations.append(f"  줄 {i+1}: ...{line[-20:]}")
        return violations

    @staticmethod
    def validate(script_text):
        results = []

        forbidden = ScriptValidator.check_forbidden_endings(script_text)
        if forbidden:
            results.append(f"[경고] 금지 어미 발견: {', '.join(forbidden)}")
        else:
            results.append("[통과] 금지 어미 없음")

        punct = ScriptValidator.check_punctuation(script_text)
        if punct:
            results.append(f"[경고] 금지 구두점 발견: {', '.join(punct)}")
        else:
            results.append("[통과] 구두점 규칙 준수")

        linebreak_issues = ScriptValidator.check_linebreaks(script_text)
        if linebreak_issues:
            results.append("[경고] 줄바꿈 위반:")
            results.extend(linebreak_issues[:5])
        else:
            results.append("[통과] 줄바꿈 규칙 준수")

        return "\n".join(results)


class ScriptGenerator:
    """명심Story v4.0 대본 생성기 (Claude API)"""

    def __init__(self, model="claude-sonnet-4-6"):
        self.client = anthropic.Anthropic()
        self.model = model
        self.validator = ScriptValidator()

    def format_news_for_prompt(self, articles):
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

    def _build_system_prompt(self, category_key):
        """시스템 프롬프트 + 카테고리 컨텍스트 조합"""
        category = CATEGORIES.get(category_key, {})
        category_name = category.get("name", category_key)

        system = SYSTEM_PROMPT
        context = CATEGORY_CONTEXT.get(category_key, {})
        if context:
            system += f"\n\n## 이번 카테고리: [{category_name}]"
            system += f"\n- 톤: {context.get('tone', '')}"
            system += f"\n- 감정 흐름: {context.get('emotion_focus', '')}"
            system += f"\n- 클로징 키워드: {context.get('closing_keyword', '')}"
            system += f"\n- 참고 패턴: {context.get('reference_pattern', '')}"

        return system

    def generate(self, articles, category_key):
        """뉴스 기사를 바탕으로 명심Story 대본 생성"""
        category = CATEGORIES.get(category_key, {})
        category_name = category.get("name", category_key)

        news_content = self.format_news_for_prompt(articles)
        system = self._build_system_prompt(category_key)

        user_prompt = SCRIPT_PROMPT_TEMPLATE.format(
            category=category_name,
            news_content=news_content,
        )

        print(f"  Claude API로 [{category_name}] 명심Story 대본 생성 중...")

        message = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user_prompt}],
        )

        full_response = message.content[0].text
        print(f"  -> 대본 생성 완료 ({len(full_response)}자)")

        # 대본 부분만 추출하여 무결성 검증
        script_section = self._extract_script_section(full_response)
        if script_section:
            validation = self.validator.validate(script_section)
            print(f"  -> 무결성 검증:\n{validation}")

        return full_response

    def _extract_script_section(self, full_response):
        """전체 응답에서 [대본] 섹션만 추출"""
        match = re.search(
            r"\[대본\]\s*\n(.*?)(?:\n\[|\Z)",
            full_response,
            re.DOTALL,
        )
        if match:
            return match.group(1).strip()
        return None

    def generate_all(self, articles_by_category):
        """모든 카테고리의 대본을 생성"""
        scripts = {}
        for cat_key, articles in articles_by_category.items():
            if not articles:
                cat_name = CATEGORIES.get(cat_key, {}).get("name", cat_key)
                print(f"  [{cat_name}] 뉴스가 없어 건너뜁니다!")
                continue
            scripts[cat_key] = self.generate(articles, cat_key)
        return scripts

    def save(self, scripts):
        """생성된 대본을 파일로 저장"""
        os.makedirs(SCRIPTS_DIR, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_files = []

        for cat_key, script_text in scripts.items():
            cat_name = CATEGORIES.get(cat_key, {}).get("name", cat_key)
            fname = f"script_{cat_key}_{timestamp}.txt"
            filepath = os.path.join(SCRIPTS_DIR, fname)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"{'=' * 50}\n")
                f.write(f"  명심Story 대본\n")
                f.write(f"  카테고리: {cat_name}\n")
                f.write(f"  생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
                f.write(f"{'=' * 50}\n\n")
                f.write(script_text)

            saved_files.append(filepath)
            print(f"  대본 저장: {filepath}")

        return saved_files
