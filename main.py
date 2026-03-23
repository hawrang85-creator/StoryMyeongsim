"""명심 스토리 - 뉴스 소재 수집 & 대본 생성기

인터랙티브 모드:
    python main.py              # 대화형으로 뉴스 수집 → 선택 → 대본 생성

명령어 모드:
    python main.py collect                        # 전체 카테고리 수집
    python main.py collect -c defense             # 국방 뉴스만 수집
    python main.py list                           # 카테고리 목록
"""

import argparse
import sys

from news_collector import CATEGORIES, NewsCollector, ScriptGenerator


def list_categories():
    """사용 가능한 카테고리 출력"""
    print("=== 뉴스 수집 카테고리 ===")
    for key, cat in CATEGORIES.items():
        keywords = ", ".join(cat["keywords"][:5])
        print(f"  {key:12s} | {cat['name']:6s} | 키워드: {keywords} ...")
    print()


def _print_articles(articles, start_num=1):
    """뉴스 기사 목록 출력 (번호 포함)"""
    for i, article in enumerate(articles, start_num):
        a = article if isinstance(article, dict) else article.to_dict()
        print(f"  [{i}] {a['title']}")
        if a.get("summary"):
            summary = a["summary"][:80] + "..." if len(a["summary"]) > 80 else a["summary"]
            print(f"      {summary}")
        print(f"      출처: {a.get('source', '')} | {a.get('published', '')}")
        print()


def _input_prompt(prompt):
    """사용자 입력받기"""
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print("\n종료합니다!")
        sys.exit(0)


def interactive_mode():
    """인터랙티브 워크플로우: 수집 → 선택 → 대본 생성"""
    print("=" * 50)
    print("  명심 스토리 - 뉴스 소재 수집 & 대본 생성기")
    print("=" * 50)
    print()

    # ── 1단계: 카테고리 선택 ──
    print("[1단계] 카테고리를 선택하세요")
    print()
    cat_keys = list(CATEGORIES.keys())
    for i, key in enumerate(cat_keys, 1):
        cat = CATEGORIES[key]
        keywords = ", ".join(cat["keywords"][:4])
        print(f"  {i}. {cat['name']} ({keywords})")
    print(f"  {len(cat_keys) + 1}. 전체 카테고리")
    print()

    while True:
        choice = _input_prompt("번호를 입력하세요: ")
        try:
            num = int(choice)
            if 1 <= num <= len(cat_keys):
                selected_cats = [cat_keys[num - 1]]
                break
            elif num == len(cat_keys) + 1:
                selected_cats = cat_keys
                break
        except ValueError:
            pass
        print("올바른 번호를 입력해주세요!")

    selected_names = [CATEGORIES[k]["name"] for k in selected_cats]
    print(f"\n선택: {', '.join(selected_names)}")
    print()

    # ── 2단계: 뉴스 수집 ──
    all_articles = _collect_news(selected_cats)

    # ── 3단계: 뉴스 선택 (반복 가능) ──
    chosen = _select_news_loop(all_articles, selected_cats)

    if not chosen:
        print("선택된 뉴스가 없습니다! 종료합니다!")
        return

    # ── 4단계: 대본 생성 ──
    _generate_script(chosen)


def _collect_news(selected_cats, method="rss", extra_keywords=None):
    """뉴스 수집 실행"""
    print("[뉴스 수집 중...]")
    print()

    collector = NewsCollector(categories=selected_cats)

    if extra_keywords:
        # 추가 키워드로 재수집
        all_articles = {}
        for cat_key in selected_cats:
            query = "+OR+".join(extra_keywords)
            url = f"https://search.naver.com/search.naver?where=news&query={query}&sort=1"
            print(f"  추가 키워드로 검색 중: {', '.join(extra_keywords)}")
            articles = collector.collect_from_naver(cat_key)
            # 키워드 기반 Google RSS도 시도
            from urllib.parse import quote
            keyword_query = "+OR+".join(extra_keywords)
            rss_url = f"https://news.google.com/rss/search?q={quote(keyword_query)}&hl=ko&gl=KR&ceid=KR:ko"
            try:
                import requests
                from bs4 import BeautifulSoup
                from news_collector.collector import NewsArticle
                resp = requests.get(rss_url, headers=collector.headers, timeout=10)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.content, "xml")
                items = soup.find_all("item")[:10]
                for item in items:
                    title = item.find("title")
                    link = item.find("link")
                    desc = item.find("description")
                    pub_date = item.find("pubDate")
                    article = NewsArticle(
                        title=title.get_text(strip=True) if title else "",
                        link=link.get_text(strip=True) if link else "",
                        summary=desc.get_text(strip=True) if desc else "",
                        published=pub_date.get_text(strip=True) if pub_date else "",
                        source="Google News",
                        category=CATEGORIES[cat_key]["name"],
                    )
                    articles.append(article)
            except Exception as e:
                print(f"  추가 검색 오류: {e}")
            all_articles[cat_key] = articles
            print(f"  -> {len(articles)}건 수집")
    else:
        all_articles = collector.collect_all(method=method)

    # 결과 표시
    total = 0
    for cat_key, articles in all_articles.items():
        cat_name = CATEGORIES[cat_key]["name"]
        print(f"\n--- [{cat_name}] {len(articles)}건 ---")
        _print_articles(articles)
        total += len(articles)

    print(f"총 {total}건 수집 완료!")
    print()

    return all_articles


def _select_news_loop(all_articles, selected_cats):
    """뉴스 선택 루프 (마음에 안 들면 재수집 가능)"""
    while True:
        # 전체 기사를 하나의 리스트로 펼침
        flat_articles = []
        for cat_key in selected_cats:
            for article in all_articles.get(cat_key, []):
                flat_articles.append((cat_key, article))

        if not flat_articles:
            print("수집된 뉴스가 없습니다!")
            retry = _input_prompt("추가 키워드로 다시 검색할까요? (y/n): ")
            if retry.lower() in ("y", "yes", "ㅛ"):
                keywords = _input_prompt("검색할 키워드를 입력하세요 (쉼표로 구분): ")
                keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
                if keyword_list:
                    all_articles = _collect_news(selected_cats, extra_keywords=keyword_list)
                    continue
            return []

        print("[2단계] 대본에 사용할 뉴스를 선택하세요")
        print()
        print("  사용법:")
        print("    번호 입력  → 해당 뉴스 선택 (예: 1 3 5)")
        print("    a 또는 all → 전체 선택")
        print("    r 또는 재검색 → 추가 키워드로 재수집")
        print()

        choice = _input_prompt("선택: ")

        # 전체 선택
        if choice.lower() in ("a", "all", "전체"):
            chosen = {}
            for cat_key, article in flat_articles:
                chosen.setdefault(cat_key, []).append(article)
            print(f"\n전체 {len(flat_articles)}건 선택 완료!")
            return chosen

        # 재검색
        if choice.lower() in ("r", "재검색", "retry"):
            keywords = _input_prompt("추가 키워드를 입력하세요 (쉼표로 구분): ")
            keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
            if keyword_list:
                all_articles = _collect_news(selected_cats, extra_keywords=keyword_list)
                continue
            else:
                print("키워드가 입력되지 않았습니다! 다시 선택해주세요!")
                continue

        # 번호 선택
        try:
            nums = [int(n) for n in choice.split()]
            chosen = {}
            for num in nums:
                if 1 <= num <= len(flat_articles):
                    cat_key, article = flat_articles[num - 1]
                    chosen.setdefault(cat_key, []).append(article)
                else:
                    print(f"  [{num}] 범위를 벗어났습니다! (1~{len(flat_articles)})")

            if chosen:
                print(f"\n선택된 뉴스 {sum(len(v) for v in chosen.values())}건:")
                for cat_key, articles in chosen.items():
                    for a in articles:
                        title = a.title if hasattr(a, "title") else a["title"]
                        print(f"  - {title}")
                print()

                confirm = _input_prompt("이 뉴스로 대본을 생성할까요? (y/n): ")
                if confirm.lower() in ("y", "yes", "ㅛ", ""):
                    return chosen
                else:
                    print("다시 선택해주세요!\n")
                    continue
        except ValueError:
            print("올바른 번호를 입력해주세요! (예: 1 3 5)")
            continue


def _generate_script(chosen_articles):
    """선택된 뉴스로 Claude API를 통해 대본 자동 생성"""
    print()
    print("=" * 50)
    print("  [3단계] 대본 생성 (Claude API)")
    print("=" * 50)
    print()

    generator = ScriptGenerator()
    scripts = generator.generate_all(chosen_articles)

    if scripts:
        saved = generator.save(scripts)
        print()
        print("=" * 50)
        print("  대본 생성 완료!")
        print("=" * 50)
        for path in saved:
            print(f"  -> {path}")
        print()
        print("명심Story 대본을 확인하세요!")
    else:
        print("생성된 대본이 없습니다!")


def cmd_collect(args):
    """뉴스 수집 실행 (명령어 모드)"""
    categories = [args.category] if args.category else None
    collector = NewsCollector(categories=categories)

    print("=" * 50)
    print("  명심 스토리 - 뉴스 소재 수집기")
    print("=" * 50)
    print()

    results = collector.collect_all(method=args.method)

    total = 0
    for cat_key, articles in results.items():
        cat_name = CATEGORIES[cat_key]["name"]
        print(f"\n--- [{cat_name}] 수집 결과 ({len(articles)}건) ---")
        _print_articles(articles)
        total += len(articles)
    print(f"\n총 {total}건의 뉴스 수집 완료")

    if not args.no_save:
        if total > 0:
            filepath = collector.save(results)
            print(f"스토리 소재로 활용하세요: {filepath}")

    return results


def main():
    parser = argparse.ArgumentParser(description="명심 스토리 - 뉴스 소재 수집 & 대본 생성기")
    subparsers = parser.add_subparsers(dest="command", help="실행할 명령")

    # collect 서브커맨드
    p_collect = subparsers.add_parser("collect", help="뉴스 수집")
    p_collect.add_argument(
        "--category", "-c",
        choices=list(CATEGORIES.keys()),
        help="수집할 카테고리",
    )
    p_collect.add_argument(
        "--method", "-m",
        choices=["rss", "naver"],
        default="rss",
        help="수집 방법 (기본: rss)",
    )
    p_collect.add_argument("--no-save", action="store_true", help="파일 저장 없이 출력만")

    # list 서브커맨드
    subparsers.add_parser("list", help="카테고리 목록 보기")

    args = parser.parse_args()

    if args.command == "collect":
        cmd_collect(args)
    elif args.command == "list":
        list_categories()
    else:
        # 명령어 없으면 인터랙티브 모드
        interactive_mode()


if __name__ == "__main__":
    main()
