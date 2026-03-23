"""명심 스토리 - 뉴스 소재 수집기

사용법:
    python main.py                    # 전체 카테고리 수집
    python main.py --category defense # 국방 뉴스만 수집
    python main.py --category technology  # 기술 뉴스만 수집
    python main.py --category k_food  # K-푸드 뉴스만 수집
    python main.py --method naver     # 네이버 뉴스 검색으로 수집
    python main.py --list             # 카테고리 목록 보기
"""

import argparse
import sys

from news_collector import CATEGORIES, NewsCollector


def list_categories():
    """사용 가능한 카테고리 출력"""
    print("=== 뉴스 수집 카테고리 ===")
    for key, cat in CATEGORIES.items():
        keywords = ", ".join(cat["keywords"][:5])
        print(f"  {key:12s} | {cat['name']:6s} | 키워드: {keywords} ...")
    print()


def main():
    parser = argparse.ArgumentParser(description="명심 스토리 - 뉴스 소재 수집기")
    parser.add_argument(
        "--category", "-c",
        choices=list(CATEGORIES.keys()),
        help="수집할 카테고리 (미지정 시 전체 수집)",
    )
    parser.add_argument(
        "--method", "-m",
        choices=["rss", "naver"],
        default="rss",
        help="수집 방법 (기본: rss)",
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="카테고리 목록 보기",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="파일 저장 없이 출력만",
    )
    args = parser.parse_args()

    if args.list:
        list_categories()
        return

    categories = [args.category] if args.category else None
    collector = NewsCollector(categories=categories)

    print("=" * 50)
    print("  명심 스토리 - 뉴스 소재 수집기")
    print("=" * 50)
    print()

    results = collector.collect_all(method=args.method)

    # 결과 출력
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

    # 저장
    if not args.no_save and total > 0:
        filepath = collector.save(results)
        print(f"스토리 소재로 활용하세요: {filepath}")


if __name__ == "__main__":
    main()
