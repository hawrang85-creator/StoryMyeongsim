"""뉴스 수집 카테고리 정의"""

CATEGORIES = {
    "defense": {
        "name": "국방",
        "keywords": ["국방", "군사", "방위", "무기", "미사일", "전투기", "해군", "육군", "공군", "방산", "K-방산"],
        "rss_feeds": [
            "https://news.google.com/rss/search?q=국방+OR+방산+OR+K방산&hl=ko&gl=KR&ceid=KR:ko",
        ],
    },
    "technology": {
        "name": "기술",
        "keywords": ["기술", "AI", "인공지능", "반도체", "IT", "스타트업", "로봇", "자율주행", "양자컴퓨터", "우주"],
        "rss_feeds": [
            "https://news.google.com/rss/search?q=기술+OR+AI+OR+반도체+OR+IT&hl=ko&gl=KR&ceid=KR:ko",
        ],
    },
    "k_food": {
        "name": "K-푸드",
        "keywords": ["K-푸드", "K푸드", "한식", "김치", "라면", "한국음식", "식품수출", "K-food", "먹거리", "한국식품"],
        "rss_feeds": [
            "https://news.google.com/rss/search?q=K푸드+OR+한식+OR+식품수출+OR+K-food&hl=ko&gl=KR&ceid=KR:ko",
        ],
    },
}
