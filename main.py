"""명심 스토리 - 뉴스 소재 수집 & 대본 생성기

사용법:
    # 뉴스 수집
    python main.py collect                        # 전체 카테고리 수집
    python main.py collect -c defense             # 국방 뉴스만 수집
    python main.py collect -c technology          # 기술 뉴스만 수집
    python main.py collect -c k_food              # K-푸드 뉴스만 수집
    python main.py collect -m naver               # 네이버 뉴스 검색으로 수집

    # 대본 생성 (뉴스 수집 후 바로 대본 생성)
    python main.py script                         # 전체 카테고리 수집 → 대본 생성
    python main.py script -c defense              # 국방 뉴스 수집 → 대본 생성
    python main.py script --from-file data/news_20260323.json  # 기존 수집 파일로 대본 생성

    # 카테고리 목록
    python main.py list
"""

import argparse

from news_collector import CATEGORIES, NewsCollector, ScriptGenerator


def list_categories():
    """사용 가능한 카테고리 출력"""
    print("=== 뉴스 수집 카테고리 ===")
    for key, cat in CATEGORIES.items():
        keywords = ", ".join(cat["keywords"][:5])
        print(f"  {key:12s} | {cat['name']:6s} | 키워드: {keywords} ...")
    print()


def cmd_collect(args):
    """뉴스 수집 실행"""
    categories = [args.category] if args.category else None
    collector = NewsCollector(categories=categories)

    print("=" * 50)
    print("  명심 스토리 - 뉴스 소재 수집기")
    print("=" * 50)
    print()

    results = collector.collect_all(method=args.method)
    _print_results(results)

    if not args.no_save:
        total = sum(len(a) for a in results.values())
        if total > 0:
            filepath = collector.save(results)
            print(f"스토리 소재로 활용하세요: {filepath}")

    return results


def cmd_script(args):
    """뉴스 수집 후 대본 생성"""
    generator = ScriptGenerator()

    if args.from_file:
        print("=" * 50)
        print("  명심Story v4.0 - 대본 생성기")
        print(f"  소스: {args.from_file}")
        print("=" * 50)
        print()

        scripts = generator.generate_from_json(args.from_file)
    else:
        categories = [args.category] if args.category else None
        collector = NewsCollector(categories=categories)

        print("=" * 50)
        print("  명심Story v4.0 - 뉴스 수집 & 대본 생성")
        print("=" * 50)
        print()

        print("[1단계] 뉴스 수집")
        results = collector.collect_all(method=args.method)
        _print_results(results)

        total = sum(len(a) for a in results.values())
        if total == 0:
            print("수집된 뉴스가 없어 대본을 생성할 수 없습니다.")
            return

        collector.save(results)

        print()
        print("[2단계] 대본 생성")
        scripts = generator.generate_all(results)

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
        print("생성된 대본이 없습니다.")


def _print_results(results):
    """수집 결과 출력"""
    total = 0
    for cat_key, articles in results.items():
        cat_name = CATEGORIES[cat_key]["name"]
        print(f"\n--- [{cat_name}] 수집 결과 ({len(articles)}건) ---")
        for i, article in enumerate(articles, 1):
            print(f"  {i}. {article.title}")
            if article.summary:
                summary = article.summary[:80] + "..." if len(article.summary) > 80 else article.summary
                print(f"     {summary}")
            print(f"     출처: {article.source} | {article.published}")
            print()
        total += len(articles)
    print(f"\n총 {total}건의 뉴스 수집 완료")


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

    # script 서브커맨드
    p_script = subparsers.add_parser("script", help="뉴스 수집 후 대본 생성")
    p_script.add_argument(
        "--category", "-c",
        choices=list(CATEGORIES.keys()),
        help="수집할 카테고리",
    )
    p_script.add_argument(
        "--method", "-m",
        choices=["rss", "naver"],
        default="rss",
        help="수집 방법 (기본: rss)",
    )
    p_script.add_argument(
        "--from-file", "-f",
        help="기존 수집 JSON 파일에서 대본 생성",
    )

    # list 서브커맨드
    subparsers.add_parser("list", help="카테고리 목록 보기")

    args = parser.parse_args()

    if args.command == "collect":
        cmd_collect(args)
    elif args.command == "script":
        cmd_script(args)
    elif args.command == "list":
        list_categories()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
