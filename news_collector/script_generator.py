"""명심Story v4.0 대본 생성 모듈 (프롬프트 저장 방식)

API 없이 동작합니다.
선택된 뉴스를 기반으로 대본 생성용 프롬프트를 만들어
파일로 저장합니다. 이 프롬프트를 Claude에 붙여넣으면 대본이 생성됩니다.
"""

import os
from datetime import datetime

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
    """명심Story v4.0 대본 생성기 (프롬프트 저장 방식)"""

    def __init__(self):
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

    def build_prompt(self, articles, category_key):
        """선택된 뉴스로 대본 생성용 전체 프롬프트 조합"""
        category = CATEGORIES.get(category_key, {})
        category_name = category.get("name", category_key)
        news_content = self.format_news_for_prompt(articles)

        # 시스템 프롬프트 + 카테고리 컨텍스트
        system = SYSTEM_PROMPT
        context = CATEGORY_CONTEXT.get(category_key, {})
        if context:
            system += f"\n\n## 이번 카테고리: [{category_name}]"
            system += f"\n- 톤: {context.get('tone', '')}"
            system += f"\n- 감정 흐름: {context.get('emotion_focus', '')}"
            system += f"\n- 클로징 키워드: {context.get('closing_keyword', '')}"
            system += f"\n- 참고 패턴: {context.get('reference_pattern', '')}"

        # 사용자 프롬프트
        user_prompt = SCRIPT_PROMPT_TEMPLATE.format(
            category=category_name,
            news_content=news_content,
        )

        # 전체 프롬프트 조합
        full_prompt = f"""[시스템 지침]
{system}

---

[대본 생성 요청]
{user_prompt}"""

        return full_prompt

    def save_prompt(self, prompt, category_key):
        """프롬프트를 파일로 저장"""
        os.makedirs(SCRIPTS_DIR, exist_ok=True)

        category_name = CATEGORIES.get(category_key, {}).get("name", category_key)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"prompt_{category_key}_{timestamp}.txt"
        filepath = os.path.join(SCRIPTS_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"{'=' * 50}\n")
            f.write(f"  명심Story 대본 생성 프롬프트\n")
            f.write(f"  카테고리: {category_name}\n")
            f.write(f"  생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"{'=' * 50}\n\n")
            f.write("이 내용을 Claude에 붙여넣으세요:\n\n")
            f.write(prompt)

        return filepath
